## Upgrading to v1.9.0

v1.9.0 upgrades `icalendar` from 5.x to 6.x and adds a new dependency (`recurring-ical-events`). If HA fails to load the integration after upgrading, the old `icalendar 5.x` package is still cached. To fix this, **restart Home Assistant twice**. If that doesn't help, run `pip install --force-reinstall "icalendar>=6.1.0,<7.0.0"` from a terminal/SSH session and restart.

---

# iCal Sensor Support for Home Assistant

This integration will create sensors for the next few future calendar events, called:

* sensor.ical_my_calendar_event_0
* sensor.ical_my_calendar_event_1
* sensor.ical_my_calendar_event_2
(...)

And it will create a calendar-entry that can be used in the calendar cards etc.

* calendar.ical_my_calendar


## Installation

Install with HACS


### Setup

The integration is set up using the GUI.

* Go to Configuration -> Integrations and click on the "+"-button.
* Search for "ical"
* Enter a name for the calendar, and the URL
* By default it will set up 5 sensors for the 5 nex upcoming events (sensor.ical_<calendar_name>_event_1 ~ 5).  You can adjust this to add more or fewer sensors
* The integration will only consider events with a start time 365 days into the future by default. This can also be adjusted when adding a new calendar

### Breaking change

If you have used this integration previously with yaml-config, you need to set up the calendars again using the GUI and adjust any scripts/automations etc. to use the new entity_ids that are generated automatically.
You can then safely remove any ical sensor and integration config from your yaml files.
