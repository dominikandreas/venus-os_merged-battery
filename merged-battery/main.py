#!/usr/bin/env python3

"""
Merges data from two existing battery services:
  - JK-BMS on com.victronenergy.battery.socketcan_can0
  - SmartShunt on com.victronenergy.battery.ttyS2
  (service paths can be specified in config.ini)

Publishes everything as a new battery service:
  - com.victronenergy.battery.<device_name> (device_name taken from config.ini)

Follows the style of Victron's DbusDummyService, but instead of dummy data,
we dynamically read from two remote D-Bus services every second.

No writes are handled: read-only bridging of BMS & SmartShunt data.
Always prefer the SmartShunt's data whenever available. Otherwise use BMS data.
"""

import configparser
import json
import logging
import os
import platform
import sys
import time
from pathlib import Path
from typing import List

SCRIPT_DIR = Path(__file__).resolve().parent

TESTING = os.environ.get("TEST_MERGED_BATTERY")

# if testing, import mock libs
if TESTING:
    from testing.mock_dbus import GLib, VeDbusService, dbus, simulate_bms, simulate_shunt

    simulate_bms()
    simulate_shunt()
else:
    import dbus
    from gi.repository import GLib

    sys.path.insert(1, str(SCRIPT_DIR / "ext/velib_python"))
    from ext.velib_python.vedbus import VeDbusService


class Config:
    device_name: str
    device_instance: int
    bms_service: str
    smartshunt_service: str
    merged_service: str
    smartshunt_paths: List[str]
    extra_bms_paths: List[str]
    update_frequency: float
    timeout: int = 60

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


try:
    config_file = os.path.join(SCRIPT_DIR, "config.ini" if not TESTING else "config.sample.ini")
    parser = configparser.ConfigParser()
    parser.read(config_file)

    missing_entries = [k for k in Config.__annotations__.keys() if k not in parser["DEFAULT"]]
    if missing_entries:
        raise ValueError(f"Missing entries in config file: {missing_entries}")

    def get_config_entry(name, type, section="DEFAULT"):
        if type is int:
            return parser.getint(section, name)
        elif type is float:
            return parser.getfloat(section, name)
        elif type is list or getattr(type, "__origin__", None) is list:
            return json.loads(parser.get(section, name))
        elif type is bool:
            return parser.getboolean(section, name)
        else:
            assert type is str, f"Unsupported type: {type}"
            return parser.get(section, name)

    config = Config(**{k: get_config_entry(k, t) for k, t in Config.__annotations__.items()})

except Exception as e:
    print(f"Error reading config file: {e}")
    time.sleep(60)
    sys.exit()


class DbusMergedBatteryService:
    def __init__(self, servicename, deviceinstance=28, productname="Merged BMS", connection="Merged JK + SmartShunt"):
        self._log = logging.getLogger("DbusMergedBatteryService")

        # 1) Instantiate with `register=False`
        self._dbusservice = VeDbusService(servicename, register=False)

        # 2) Add your mandatory & custom paths
        self._dbusservice.add_path("/Mgmt/ProcessName", __file__)
        self._dbusservice.add_path(
            "/Mgmt/ProcessVersion", f"Unknown version, running on Python {platform.python_version()}"
        )
        self._dbusservice.add_path("/Mgmt/Connection", connection)

        self._dbusservice.add_path("/DeviceInstance", deviceinstance)
        self._dbusservice.add_path("/ProductId", 0)
        self._dbusservice.add_path("/ProductName", productname)
        self._dbusservice.add_path("/FirmwareVersion", "0.1.0-dev (20241223)")
        self._dbusservice.add_path("/HardwareVersion", 0)
        self._dbusservice.add_path("/Connected", 1)

        # If you have a set of additional paths to publish:
        for p in config.smartshunt_paths + config.extra_bms_paths:
            if p not in self._dbusservice._dbusobjects:
                self._dbusservice.add_path(p, value=None, writeable=True)

        # 3) Now register all at once
        self._dbusservice.register()

        # set up your GLib timer callback, etc.
        GLib.timeout_add(int(config.update_frequency * 1000), self._update)

        self._log.info(f"Started {servicename} as DeviceInstance={deviceinstance}")

    def _update(self):
        """Read data from JK-BMS & SmartShunt, merge it, and update the service."""
        bms_data = self._read_paths(config.bms_service, config.extra_bms_paths)
        shunt_data = self._read_paths(config.smartshunt_service, config.smartshunt_paths)

        # Start merged_data as a copy of the BMS
        merged_data = dict(bms_data)
        merged_data["/Connected"] = 1

        # Overwrite with SmartShunt data if available
        if shunt_data.get("/Connected") == 1:
            for path in config.smartshunt_paths:
                if path in shunt_data and shunt_data[path] is not None:
                    merged_data[path] = shunt_data[path]

        # Now push final data into our own service
        for path, val in merged_data.items():
            try:
                self._dbusservice[path] = val
            except Exception as e:
                self._log.exception(
                    f"exception occurred for {path}: {e}\n:"
                    + (json.dumps(val, indent=4) if isinstance(val, dict) else val),
                )
                time.sleep(config.timeout)
                exit()

        merged_data["/ProductName"] = config.device_name

        self._log.debug(f"merged result: \n{ json.dumps(merged_data, indent=4) }")

        return True  # return True so GLib keeps calling us

    def _read_paths(self, service_name, path_names):
        """Read each path from the remote service, returning a dict {path: value or None}."""
        result = {}
        bus = dbus.SystemBus()
        try:
            remote = bus.get_object(service_name, "/")
            # We'll use the com.victronenergy.BusItem interface for each path
            bus_item = dbus.Interface(remote, "com.victronenergy.BusItem")

            bus_data = bus_item.GetValue("/")
            self._log.debug(f"got bus_data for {service_name}:\n", json.dumps(bus_data, indent=2))
            result = {p: bus_data[p[1:]] for p in path_names if p[1:] in bus_data}

            self._log.debug(f"extracted result: \n{ json.dumps(result, indent=4) }")
        except dbus.DBusException as e:
            self._log.exception(f"Unable to connect to dbus service {service_name}: {e}")
            time.sleep(config.timeout)
            exit()

        return result


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.info("Starting DbusMergedBatteryService")

    if not os.environ.get("TEST_MERGED_BATTERY"):
        from dbus.mainloop.glib import DBusGMainLoop

        DBusGMainLoop(set_as_default=True)

    # Create the merged service
    DbusMergedBatteryService(
        servicename=config.merged_service,
        deviceinstance=config.device_instance,  # Read from config
        productname=config.device_name,  # Read from config
        connection="Merged driver script",
    )

    logger.info("Mainloop starting, merged D-Bus service is running.")
    mainloop = GLib.MainLoop()
    mainloop.run()


if __name__ == "__main__":
    main()
