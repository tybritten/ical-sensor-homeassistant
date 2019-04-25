# iCal Sensor Support for Home Assistant

in your configuration.yaml you'll need:

```
sensor:
- platform: ical
  name: "My Calendar"
  url: "http://url.to/ical"
```

It will create sensors for the next few future calendar events, called:

* sensor.my_calendar_event_0
* sensor.my_calendar_event_1
* sensor.my_calendar_event_2

etc

## Manual Installation

Put the keys file (sensor.py, __init__.py and manifest.json) in your home-assistant config directory under custom_components/ical.

## Custom Updater

[ical_updater.json](ical_updater.json)  provide the details Custom Updater needs. See [Custom Updater Installation](https://github.com/custom-components/custom_updater/wiki/Installation) to install it.

### Setup

Add the following to your configuration:
```
custom_updater:
  track:
    - components
  component_urls:
    - https://raw.githubusercontent.com/tybritten/ical-sensor-homeassistant/master/ical_updater.json

```

### Installing

To install it for the first time, use the [`custom_updater.install`](https://github.com/custom-components/custom_updater/wiki/Services#install-element-cardcomponentpython_script) service with appropriate service data:
```
{
  "element": "ical-sensor-bundle"
}
```

### Updating

Once the iCal component is installed it can easily be updated using the [Tracker card](https://github.com/custom-cards/tracker-card). If you're not using the Tracker card then you can use the [`custom_updater.update_all`](https://github.com/custom-components/custom_updater/wiki/Services#update-all) service.

