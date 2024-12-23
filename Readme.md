# Merged-Battery

A Venus-OS driver to merge information from a SmartShunt and a BMS by taking all information from the BMS and overriding available information from the SmartShunt.

This allows to benefit from the detailed information coming from the BMS and the more precise readings from the SmartShunt like current, power and state of charge.

## Index

- [Merged-Battery](#merged-battery)
  - [Index](#index)
  - [Disclaimer](#disclaimer)
  - [Config](#config)
  - [Install / Update](#install--update)
    - [Extra steps for your first installation](#extra-steps-for-your-first-installation)
  - [Restart / Uninstall](#restart--uninstall)
  - [Debugging](#debugging)
  - [Compatibility](#compatibility)
  - [Supporting/Sponsoring this project](#supportingsponsoring-this-project)

## Disclaimer

I wrote this script for myself. I'm not responsible, if you damage something using my script.

## Config

Edit the config.ini and change the defaults as required.

At minimum, you should check / edit the service name entries:

```ini
; BMS service name
bms_service = com.victronenergy.battery.socketcan_can0

; SmartShunt service name
smartshunt_service = com.victronenergy.battery.ttyS2
```

These depend on the connection port of your BMS / SmartShunt.

You can find the service names and available paths via `dbus-spy`, a dbus utility that comes pre-installed on venus-os and allows to inspect the different services that are available.

The remaining setting control the paths that are reflected into the merged service. The paths from the SmartShunt service take precedence and will overwrite any paths from the BMS Service (except when the SmartShunt is for some reason not connected).

## Install / Update

1. Login to your Venus OS device via SSH. See [Venus OS:Root Access](https://www.victronenergy.com/live/ccgx:root_access#root_access) for more details.

2. Execute this commands to download and copy the files:

    ```bash
    wget -O /tmp/download_merged_battery.sh https://raw.githubusercontent.com/dominikandreas/venus-os_merged-battery/master/download.sh

    bash /tmp/download_merged_battery.sh
    ```

3. Select the version you want to install.

4. Press enter for a single instance. For multiple instances, enter a number and press enter.

    Example:

    - Pressing enter or entering `1` will install the driver to `/data/etc/merged-battery`.
    - Entering `2` will install the driver to `/data/etc/merged-battery-2`.

### Extra steps for your first installation

1. Edit the config.ini to fit your needs. The correct command for your installation is shown after the installation.

    - If you pressed enter or entered `1` during installation:

    ```bash
    nano /data/etc/merged-battery/config.ini
    ```

    - If you entered `2` during installation:

    ```bash
    nano /data/etc/merged-battery-2/config.ini
    ```

2. Install the driver as a service. The correct command for your installation is shown after the installation.

    - If you pressed enter or entered `1` during installation:

    ```bash
    bash /data/etc/merged-battery/install.sh
    ```

    - If you entered `2` during installation:

    ```bash
    bash /data/etc/merged-battery-2/install.sh
    ```

    The daemon-tools should start this service automatically within seconds.

## Restart / Uninstall

Simply run the `restart` / `uninstall.sh` script:

```bash
bash /data/etc/merged-battery/uninstall.sh
```

(adapt the `/merged-battery/` path depending on your installation)

## Debugging

The log can be shown via:

```bash
tail -n 100 -F /data/log/merged-battery/current | tai64nlocal
```

(adapt the `/merged-battery/` path depending on your installation)

The service status can be checked with svstat `svstat /service/merged-battery`

This will output somethink like `/service/merged-battery: up (pid 5845) 185 seconds`

If the seconds are under 5 then the service crashes and gets restarted all the time. If you do not see anything in the logs you can increase the log level in `/data/etc/merged-battery/merged-battery.py` by changing `level=logging.WARNING` to `level=logging.INFO` or `level=logging.DEBUG`

If the script stops with the message `dbus.exceptions.NameExistsException: Bus name already exists: com.victronenergy.pvinverter.mqtt_pv"` it means that the service is still running or another service is using that bus name.

## Compatibility

This software was only tested on Venus OS v3.52. It will likely also work on others versions.

## Supporting/Sponsoring this project

You like the project and consider supporting [Mr Manuel](https://github.com/mr-manuel), I took most of the boiler plate code from him:

[![Donate](https://github.md0.eu/uploads/donate-button.svg)](https://www.paypal.com/donate/?hosted_button_id=3NEVZBDM5KABW)
