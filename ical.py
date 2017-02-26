"""
Support for iCal-URLs

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.ical/
"""
import logging
from datetime import timedelta
import datetime as dt
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity

import icalendar, requests, arrow


_LOGGER = logging.getLogger(__name__)
REQUIREMENTS = ['icalendar', 'requests', 'arrow>=0.10.0']

ICON = 'mdi:calendar'
DEFAULT_NAME = 'iCal Sensor'
DEFAULT_MAX_EVENTS = 5

# Return cached results if last scan was less then this time ago.
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=120)


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Setup the iCal Sensor."""
    url = config.get('url')
    name = config.get('name', DEFAULT_NAME)
    maxevents = config.get('maxevents',DEFAULT_MAX_EVENTS)

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
        sensors.append(ICalSensor(hass,data_object,eventnumber))

    add_devices_callback(sensors)

   # add_devices_callback([ICalSensor(hass, data_object,name)])

def dateparser(calendar,date):
    events = []
    for event in calendar.walk('VEVENT'):
        if type(event['DTSTART'].dt) is dt.date:
            start = arrow.get(event['DTSTART'].dt)
            start = start.replace(tzinfo='local')
        else: start = event['DTSTART'].dt
        if type(event['DTEND'].dt) is dt.date:
            end = arrow.get(event['DTEND'].dt)
            end = end.replace(tzinfo='local')
        else: end = event['DTEND'].dt
        if start.date() >= date.date():
            events.append(dict(name=event['SUMMARY'],begin=start))
    sorted_events = sorted(events, key=lambda k: k['begin'])
    _LOGGER.info(sorted_events)
    return sorted_events

# pylint: disable=too-few-public-methods
class ICalSensor(Entity):
    """Implementation of a iCal sensor."""
    def __init__(self, hass, data_object, eventnumber):
        """Initialize the sensor."""
        self._eventno = eventnumber
        self._hass = hass
        self.data_object = data_object
        self._name = 'event_' + str(eventnumber)
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

    def update(self):
        """Get the latest update and set the state."""
        self.data_object.update()
        e = self.data_object.data
        if self._eventno not in range(0,len(e)):
            self._state = "No event"
        else:
            if not e:
                self._state = "No event"
            else:
                val = e[self._eventno]
                self._state = "{} - {}".format( val['name'], val['begin'].strftime("%-d %B %Y %H:%M"))

#pylint: disable=too-few-public-methods
class ICalData(object):
    """Class for handling the data retrieval."""

    def __init__(self, resource):
        self._request = requests.Request('GET', resource).prepare()
        self.data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        self.data = []

        try:
            with requests.Session() as sess:
                response = sess.send(self._request, timeout=10)

            cal = icalendar.Calendar.from_ical(response.text)
            today = arrow.utcnow()
            events = dateparser(cal,today)

            self.data = events

        except requests.exceptions.RequestException:
            _LOGGER.error("Error fetching data: %s", self._request)
            self.data = None
