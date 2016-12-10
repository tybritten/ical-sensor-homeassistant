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

# Return cached results if last scan was less then this time ago.
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=120)


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Setup the iCal Sensor."""
    url = config.get('url')
    name = config.get('name', DEFAULT_NAME)

    if url is None:
        _LOGGER.error('Missing required variable: "url"')
        return False

    data_object = ICalData(url)
    data_object.update()

    if data_object.data is None:
        _LOGGER.error('Unable to fetch iCal')
        return False

    add_devices_callback([ICalSensor(hass, data_object,
                                          name)])

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
        if start <= date <= end:
            events.append(dict(name=event['SUMMARY'],begin=start))
    return events

# pylint: disable=too-few-public-methods
class ICalSensor(Entity):
    """Implementation of a iCal sensor."""
    def __init__(self, hass, data_object, name):
        """Initialize the sensor."""
        self._hass = hass
        self.data_object = data_object
        self._name = name
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

        if not e:
            self._state = "No event today"
        else:
            self._state = "{} - {}".format(e['begin'].humanize(), e['name'])

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

            if not events:
                tomorrow = today.replace(days=+1)
                events = dateparser(cal,tomorrow)

                if events:
                    self.data = events[0]
            else:
                self.data = events[0]

        except requests.exceptions.RequestException:
            _LOGGER.error("Error fetching data: %s", self._request)
            self.data = None