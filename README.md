# OVO Charge (Bonnet) Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

This is a custom integration for [Home Assistant](https://www.home-assistant.io/) to integrate with [OVO Charge (formerly Bonnet)](https://www.ovo-charge.com/). It allows you to monitor your electric vehicle charging sessions in real-time.

This integration uses an unofficial, reverse-engineered API based on the OVO Charge mobile app. As such, it may break at any time if the API is changed by the provider.

## Features

- ~~**Real-time Charging Status**: Get live updates on your charging session.~~
- **Energy Monitoring**: Track the total energy delivered to your vehicle.
- **Power Monitoring**: See the current charging power in kW.
- **Session Information**: View details like location, operator, and start time.

## Installation

### Recommended: HACS

1.  Go to HACS -> Integrations.
2.  Click the three dots in the top right and select "Custom repositories".
3.  Add the URL to this repository (`https://github.com/cvl01/ha-ovo-charge`) as an "Integration" type.
4.  Click "ADD".
5.  The "OVO Charge (Bonnet)" integration will now be available to install. Click "INSTALL".
6.  Restart Home Assistant.

### Manual Installation

1.  Copy the `custom_components/ovo_charge` directory to your Home Assistant `custom_components` directory.
2.  Restart Home Assistant.

## Configuration

Configuration is done via the Home Assistant UI.

1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration** and search for **OVO Charge (Bonnet)**.
3.  You will be asked for your OVO Charge email address. Enter it and click **Submit**.
4.  The integration will send a "magic link" to your email address.
5.  Check your email inbox for an email from OVO Charge / Bonnet.
6.  **Right-click** the login button/link in the email and **copy the full link address**.
7.  Paste the entire link into the "Magic Link" field in Home Assistant and click **Submit**.
8.  The integration will be configured and a new device will be added to Home Assistant.

## Sensors

The integration will create a device named "OVO Charge" with the following sensors:

| Sensor          | Description                                         |
| --------------- | --------------------------------------------------- |
| Status          | The current status of the charging session.         |
| Energy          | Total energy delivered in the session (kWh).        |
| Power           | Current charging power (kW).                        |
| Cost            | Total cost of the charging session.                 |

The `Status` sensor also provides additional attributes such as:
- Address
- Operator
- Start Time
- Currency
- Total Cost
- Command ID

## Disclaimer

This project is not affiliated with, endorsed by, or in any way officially connected with OVO Charge or Bonnet.

## Issues

If you have any issues, please [report them on GitHub](https://github.com/cvl01/ha-ovo-charge/issues). 