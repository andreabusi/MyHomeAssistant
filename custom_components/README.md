# Custom Components

These are the custom components actually installed on HA:

## Third party components

### `alexa_media`

Control Amazon Alexa devices in HomeAssistant using the unofficial Alexa API.

* [GitHub repo](https://github.com/custom-components/alexa_media_player)
* Installed version: 2.10.1
* Updated on: 12/08/2020

### `sonoff`

Simple Home Assistant component to add/control Sonoff/eWeLink smart devices using the stock firmware and retaining the cloud capabilities.

* [GitHub repo](https://github.com/peterbuga/HASS-sonoff-ewelink)
* Installed version: 0.3.3
* Updated on: 25/11/2019

### `mitemp_bt`

Custom integration for Xiamo Temparature Sensor, due to unreliability of the standard integration.

This custom component is an alternative for the standard build in mitemp_bt integration that is available in Home Assistant. Unlike the original mitemp_bt integration, which is getting its data by polling the device with a default five-minute interval, this custom component is parsing the Bluetooth Low Energy packets payload that is constantly emitted by the sensor.

* [GitHub repo](https://github.com/custom-components/sensor.mitemp_bt)
* Installed version: 0.6.5
* Updated on: 21/04/2020

### `shelly`

Adds components for Shelly smart home devices to Home Assistant. There is no configuration needed, it will find all devices on your LAN and add them to Home Assistant. All communication with Shelly devices is local. You can use this plugin and continue to use Shelly Cloud, MQTT and Shelly app in your mobile if you want.

* [GitHub repo](https://github.com/StyraHem/ShellyForHASS)
* Installed version: 0.1.8
* Updated on: 26/05/2020

## Self made

### `magpi_download`

Check and download the latest number of MagPi Magazine.

* Updated on: 22/04/2020

### `home_recycling`

Update sensors for the home recycling, based on the provided city calendar.
