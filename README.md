# Italian Rail Monitor

Home Assistant custom integration for monitoring Italian trains.

> **Work in progress:** this project is an early prototype. It is not yet a
> stable release and has not been submitted to the HACS default repository.

## Current status

The integration configures a train by its number and ViaggiaTreno origin-station
code, then lets the user select the boarding station from the stops returned
for that train. It exposes the general reported delay, an estimated delay for
the selected boarding station, and the planned arrival platform.

The boarding-station delay estimate is updated using the actual departure
delay at the most recently departed station before the selected boarding stop.
It is an indicative carry-forward estimate, not an official arrival prediction.
If a newer preceding station has no actual departure yet, the last available
actual departure remains the source.

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
- [x] Select the boarding station from the train's route stops
- [x] Estimate boarding-station delay from the latest actual preceding departure
- [x] Expose the planned arrival platform at the boarding station
- [ ] Validate estimate updates across multiple live station transits
- [ ] Cancellation and suppressed-stop detection
- [ ] Configurable delay threshold and notifications
- [ ] Additional providers and operators

## Disclaimer

This is an independent community project and is not affiliated with
Trenitalia, Trenord, RFI, or the ViaggiaTreno service.
