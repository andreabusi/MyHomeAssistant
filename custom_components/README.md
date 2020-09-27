# Custom Components

These are the custom components actually installed on HA:

## Third party components

### `alexa_media`

Control Amazon Alexa devices in HomeAssistant using the unofficial Alexa API.

* [GitHub repo](https://github.com/custom-components/alexa_media_player)
* Installed version: 3.0.1
* Updated on: 27/09/2020

### `SonoffLAN`

Home Assistant custom component for control Sonoff devices with eWeLink (original) firmware over LAN and/or Cloud.

* [GitHub repo](https://github.com/AlexxIT/SonoffLAN)
* Installed version: 2.3.1
* Updated on: 22/09/2020

### `mitemp_bt`

Custom integration for Xiamo Temparature Sensor, due to unreliability of the standard integration.

This custom component is an alternative for the standard build in mitemp_bt integration that is available in Home Assistant. Unlike the original mitemp_bt integration, which is getting its data by polling the device with a default five-minute interval, this custom component is parsing the Bluetooth Low Energy packets payload that is constantly emitted by the sensor.

* [GitHub repo](https://github.com/custom-components/sensor.mitemp_bt)
* Installed version: 0.6.5
* Updated on: 21/04/2020

### `shelly4hass`

Adds components for Shelly smart home devices to Home Assistant. There is no configuration needed, it will find all devices on your LAN and add them to Home Assistant. All communication with Shelly devices is local. You can use this plugin and continue to use Shelly Cloud, MQTT and Shelly app in your mobile if you want.

* [GitHub repo](https://github.com/StyraHem/ShellyForHASS)
* Installed version: 0.2.0
* Updated on: 27/09/2020

## Self made

### `magpi_download`

Check and download the latest number of MagPi Magazine.

* Updated on: 22/04/2020

### `home_recycling`

Update sensors for the home recycling, based on the provided city calendar.
