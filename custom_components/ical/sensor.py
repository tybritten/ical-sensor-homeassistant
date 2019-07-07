"""
Support for iCal-URLs

"""
import datetime as dt
import logging
from datetime import timedelta

import requests

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)
REQUIREMENTS = ['icalendar', 'requests', 'arrow>=0.10.0']

VERSION = "0.2"
ICON = 'mdi:calendar'
DEFAULT_NAME = 'iCal Sensor'
DEFAULT_MAX_EVENTS = 5
PLATFORM = 'ical'
SCAN_INTERVAL = timedelta(minutes=1)

# Return cached results if last scan was less then this time ago.
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=120)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the iCal Sensor."""
    url = config.get('url')
    name = config.get('name', DEFAULT_NAME)
    maxevents = config.get('maxevents', DEFAULT_MAX_EVENTS)

    if url is None:
        _LOGGER.error('Missing required variable: "url"')
        return False

    data_object = ICalData(url)
    data_object.update()

    if data_object.data is None:
        _LOGGER.error('Unable to fetch iCal')
        return False

    sensors = []
    for eventnumber in range(maxevents):
        sensors.append(ICalSensor(hass, data_object, name, eventnumber))

    add_entities(sensors)


def dateparser(calendar, date):
    """
    Takes a calendar and a date, and returns a sorted list
    of events on or after that date.
    """
    import arrow
    events = []
    for event in calendar.walk('VEVENT'):

        if isinstance(event['DTSTART'].dt, dt.date):
            start = arrow.get(event['DTSTART'].dt)
            start = start.replace(tzinfo='local')
        else:
            start = event['DTSTART'].dt

        # Skip this event if it's in the past
        if start.date() < date.date():
            continue

        event_dict = {
            'name': event['SUMMARY'],
            'start': start
        }
        # Add the end info if present.
        if 'DTEND' in event:
            if isinstance(event['DTEND'].dt, dt.date):
                end = arrow.get(event['DTEND'].dt)
                end = end.replace(tzinfo='local')
            else:
                end = event['DTEND'].dt
            event_dict['end'] = end

        events.append(event_dict)

    sorted_events = sorted(events, key=lambda k: k['start'])
    _LOGGER.debug(sorted_events)
    return sorted_events


# pylint: disable=too-few-public-methods
class ICalSensor(Entity):
    """
    Implementation of a iCal sensor.
    Represents the Nth upcoming event.
    May have a name like 'sensor.mycalander_event_0' for the first
    upcoming event.
    """
    def __init__(self, hass, data_object, sensor_name, eventnumber):
        """
        Initialize the sensor.
        sensor_name is typically the name of the calendar.
        eventnumber indicates which upcoming event this is, starting at zero
        """
        self._eventno = eventnumber
        self._hass = hass
        self.data_object = data_object
        self._name = sensor_name + '_event_' + str(eventnumber)
        self._event_attributes = {}
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return ICON

    @property
    def state(self):
        """Return the date of the next event."""
        return self._state

    @property
    def device_state_attributes(self):
        """The name and date of the event."""
        return self._event_attributes

    def update(self):
        """Get the latest update and set the state and attributes."""
        # Defaults:
        self._state = "No event"
        # I guess the number and details of attributes probably
        # shouldn't change, so we should really prepopulate them.
        self._event_attributes = {
            'name': None,
            'start': None,
            'end': None
        }
        # Get the data
        self.data_object.update()

        event_list = self.data_object.data
        if event_list and (self._eventno < len(event_list)):
            val = event_list[self._eventno]
            start = val['start'].datetime
            self._event_attributes['start'] = start
            name = val.get('name', 'unknown')
            self._event_attributes['name'] = name
            self._state = "{} - {}".format(
                name,
                start.strftime("%-d %B %Y %H:%M")
            )


# pylint: disable=too-few-public-methods
class ICalData(object):
    """
    Class for handling the data retrieval.
    The 'data' field is the sorted list of future events.
    """

    def __init__(self, resource):
        self._request = requests.Request('GET', resource).prepare()
        self.data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        import arrow
        import icalendar

        self.data = []

        try:
            with requests.Session() as sess:
                response = sess.send(self._request, timeout=10)

            cal = icalendar.Calendar.from_ical(response.text)
            today = arrow.utcnow()
            events = dateparser(cal, today)

            self.data = events

        except requests.exceptions.RequestException:
            _LOGGER.error("Error fetching data: %s", self._request)
            self.data = None
