# Italian Rail Monitor

Home Assistant custom integration for monitoring Italian trains.

> **Work in progress:** this project is an early prototype. It is not yet a
> stable release and has not been submitted to the HACS default repository.

## Current status

The integration supports configuring a train by its train number and
ViaggiaTreno origin-station code. It exposes the general reported delay and a
separate sensor for the current arrival-delay value reported for a configurable
boarding station. The boarding station is selected in the integration options.

The first development target is validating live train monitoring with services
in the Morbegno–Milano corridor. The integration is being designed so that
additional data providers and Italian rail operators can be added separately.

## Data source

The first adapter uses endpoints currently used by the ViaggiaTreno website.
These endpoints are not an official, guaranteed public API. They may change,
become unavailable, or impose access restrictions. Data coverage depends on
the service and operator.

## Installation

This repository can be added to HACS as a custom repository (Integration).
The project remains experimental and should be tested before relying on it for
travel decisions.

## Development

The integration is located in
`custom_components/italian_rail_monitor/`.

## Roadmap

- [x] Initial Home Assistant integration structure
- [x] ViaggiaTreno train lookup and status client
- [x] Separate sensor for the configured boarding stop's reported arrival delay
- [ ] Validate forecast updates while a train is approaching the boarding station
- [ ] Improve delay estimation using the last detected station and observed delay
- [ ] Cancellation and suppressed-stop detection
- [ ] Configurable delay threshold and notifications
- [ ] Station and service search
- [ ] Additional providers and operators

## Disclaimer

This is an independent community project and is not affiliated with
Trenitalia, Trenord, RFI, or the ViaggiaTreno service.
