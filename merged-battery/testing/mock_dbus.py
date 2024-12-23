import traceback
from dataclasses import InitVar, dataclass, field
from threading import Thread
from time import perf_counter, sleep

services = {}


@dataclass
class VeDbusService:
    name: str
    paths: dict = field(init=False, default_factory=dict)
    register: InitVar[bool] = True

    def __post_init__(self, register):
        services[self.name] = self.paths

    def add_path(self, name, value, gettextcallback=None, writeable=False, onchangecallback=None):
        self.paths[name] = value
        print(f"add_path: {name} = {value}")

    def __getitem__(self, name):
        return self.paths[name]

    def __setitem__(self, name, value):
        self.paths[name] = value
        print(f"Updated {self.name}: {name} = {value}")

    @property
    def _dbusobjects(self):
        return self.paths

    def register(self):
        pass


@dataclass
class DbusObject:
    service_name: str

    def GetValue(self, path):
        # path is ignored
        return {p[1:]: v for p, v in services.get(self.service_name, {}).items()}


class dbus:
    @classmethod
    def SystemBus(cls):
        return cls

    @classmethod
    def get_object(cls, service_name, path="/"):
        return DbusObject(service_name)

    def Interface(remote, interface):
        return remote

    class DBusException(Exception):
        pass


class GLibFactory:
    def __init__(self):
        self.callbacks = {}
        self.last_calls = {}

    def timeout_add(self, interval, callback):
        self.callbacks[callback.__name__] = (callback, interval)

    def _main_loop(self, iters=None):
        iter = 0
        while True:
            for callback, interval in self.callbacks.values():
                last_call = self.last_calls.get(callback.__name__, 0)
                if perf_counter() - last_call < interval / 1000:  # Corrected to use perf_counter
                    continue

                print(f"Executing callback: {callback.__name__}")
                try:
                    callback()
                except Exception as e:
                    print(f"exception occurred for {callback.__name__}", e)
                    traceback.print_exc()

                self.last_calls[callback.__name__] = perf_counter()  # Corrected to use perf_counter
                sleep(0.1)
            sleep(0.1)
            iter += 1
            if iters is not None and iter >= iters:
                break

    def MainLoop(self):
        class Runner:
            def run(_self, iters=None):
                t = Thread(target=self._main_loop, args=(iters,))
                t.start()
                t.join()

        return Runner()


GLib = GLibFactory()


class BMSSimulator:
    def __init__(self):
        self._dbusservice = VeDbusService("com.victronenergy.battery")

    def add_path(self, name, init, gettextcallback=None, writeable=False, onchangecallback=None):
        self._dbusservice.add_path(name, init, gettextcallback, writeable, onchangecallback)

    def register(self):
        pass

    def __getitem__(self, name):
        return self._dbusservice[name]

    def __setitem__(self, name, value):
        self._dbusservice[name] = value

    def run(self):
        pass


def simulate_bms():
    bms_service = VeDbusService("com.victronenergy.battery.socketcan_can0")
    paths = [
        "/Alarms/ChargeBlocked",
        "/Alarms/DischargeBlocked",
        "/Alarms/CellImbalance",
        "/Alarms/HighChargeTemperature",
        "/Alarms/LowChargeTemperature",
        "/Alarms/HighDischargeCurrent",
        "/Alarms/HighChargeCurrent",
        "/Alarms/LowVoltage",
        "/Alarms/HighVoltage",
        "/Alarms/LowTemperature",
        "/Alarms/HighTemperature",
        "/Connected",
        "/ConnectionInformation",
        "/CustomName",
        "/Dc/0/Power",
        "/Dc/0/Current",
        "/Dc/0/Voltage",
        "/DeviceInstance",
        "/Family",
        "/FirmwareVersion",
        "/Info/BatteryLowVoltage",
        "/Info/ChargeRequest",
        "/Info/FullChargeRequest",
        "/Info/MaxChargeVoltage",
        "/Info/MaxChargeCurrent",
        "/Info/MaxDischargeCurrent",
        "/InstalledCapacity",
        "/Manufacturer",
        "/Redetect",
        "/Serial",
        "/Soh",
        "/Soc",
        "/Sense/Current",
        "/Sense/Voltage",
        "/Sense/Temperature",
        "/Sense/Soc",
        "/System/MaxCellTemperature",
        "/System/MinCellTemperature",
        "/System/MaxCellVoltage",
        "/System/MinCellVoltage",
        "/System/MaxTemperatureCellId",
        "/System/MinTemperatureCellId",
        "/System/MaxVoltageCellId",
        "/System/MinVoltageCellId",
        "/System/NrOfModulesBlockingCharge",
        "/System/NrOfModulesBlockingDischarge",
        "/System/NrOfModulesOnline",
        "/System/NrOfModulesOffline",
    ]
    for path in paths:
        bms_service.add_path(path, 0)

    def update_bms():
        bms_service["/Connected"] = 1
        bms_service["/Dc/0/Power"] = 520
        bms_service["/Dc/0/Current"] = 10
        bms_service["/Dc/0/Voltage"] = 52.0
        bms_service["/System/NrOfModulesOnline"] = 1
        bms_service["/Info/MaxChargeVoltage"] = 55.0
        bms_service["/Info/MaxChargeCurrent"] = 100.0
        bms_service["/Info/MaxDischargeCurrent"] = 100.0
        bms_service["/Soc"] = 50
        bms_service["/TimeToGo"] = 7100

    GLib.timeout_add(3000, update_bms)


def simulate_shunt():
    shunt_service = VeDbusService("com.victronenergy.battery.ttyS2")
    paths = [
        "/Connected",
        "/ConsumedAmpHours",
        "/Dc/0/Current",
        "/Dc/0/MidVoltage",
        "/Dc/0/MidVoltageDeviation",
        "/Dc/0/Power",
        "/Dc/0/Temperature",
        "/Dc/0/Voltage",
        "/Dc/1/Voltage",
        "/Soc",
    ]
    for path in paths:
        shunt_service.add_path(path, 0)

    def update_shunt():
        shunt_service["/Connected"] = 1
        shunt_service["/ConsumedAmpHours"] = 11
        shunt_service["/Dc/0/Current"] = 11
        shunt_service["/Dc/0/MidVoltage"] = 0
        shunt_service["/Dc/0/MidVoltageDeviation"] = 0
        shunt_service["/Dc/0/Power"] = 572
        shunt_service["/Dc/0/Temperature"] = 25.0
        shunt_service["/Dc/0/Voltage"] = 52.0
        shunt_service["/Soc"] = 51
        shunt_service["/TimeToGo"] = 7200

    GLib.timeout_add(2000, update_shunt)


if __name__ == "__main__":
    simulate_bms()
    simulate_shunt()
    GLib.MainLoop().run()
