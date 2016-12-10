#iCal Sensor Support for Home Assistant

Put this file (ical.py) in your home-assistant config directory under custom_components/sensors.
in your configuration.yaml you'll need:

```
sensor:
- platform: ical
  name: "My Calendar"
  url: "http://url.to/ical"
```