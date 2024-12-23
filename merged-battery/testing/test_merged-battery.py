import logging
import os
from unittest import TestCase

os.environ["TEST_MERGED_BATTERY"] = "1"
from main import DbusMergedBatteryService, config, dbus
from testing.mock_dbus import GLib


class TestMergedBattery(TestCase):
    def test_merging_result(self):
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger()
        logger.info("Starting DbusMergedBatteryService")

        # Create the merged service
        DbusMergedBatteryService(
            servicename=config.merged_service,
            deviceinstance=config.device_instance,  # Read from config
            productname=config.device_name,  # Read from config
            connection="Merged driver script",
        )

        logger.info("Mainloop starting, merged D-Bus service is running.")
        mainloop = GLib.MainLoop()
        mainloop.run(2)

        bus = dbus.SystemBus()
        remote = bus.get_object(config.merged_service, "/")
        # We'll use the com.victronenergy.BusItem interface for each path
        interface = dbus.Interface(remote, "com.victronenergy.BusItem")

        merged_data = interface.GetValue("/")

        assert merged_data["Connected"] == 1
        assert merged_data["ProductName"] == config.device_name
        assert merged_data["Dc/0/Voltage"] == 52.0
        assert merged_data["Dc/0/Current"] == 11.0
        assert merged_data["Dc/0/Power"] == 572.0
        assert merged_data["Dc/0/Temperature"] == 25.0
        assert merged_data["Soc"] == 51
        assert merged_data["TimeToGo"] == 7200.0
        assert merged_data["ConsumedAmpHours"] == 11.0
        assert merged_data["System/NrOfModulesOnline"] == 1
        assert merged_data["Info/MaxChargeVoltage"] == 55.0
        assert merged_data["Info/MaxChargeCurrent"] == 100.0
        assert merged_data["Info/MaxDischargeCurrent"] == 100.0


if __name__ == "__main__":
    TestMergedBattery().test_merging_result()
