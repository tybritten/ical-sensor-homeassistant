"""
Support for iCal-URLs

"""
import datetime as dt
import pytz
import logging
from datetime import timedelta
from dateutil.rrule import rrulestr, rruleset


import requests

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)
REQUIREMENTS = ['icalendar', 'requests', 'arrow>=0.10.0']

VERSION = "0.6"
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


def datefixer(indate, timezone = 'UTC'):
    """
    Takes something that looks kind of like a date
    and returns a timezone-aware datetime-object back
    """

    _LOGGER.debug("Fixing date:")
    _LOGGER.debug(indate)
    _LOGGER.debug("In TZ:")
    _LOGGER.debug(timezone)

    # Indate can be a single entry or a list...
    if isinstance(indate, list):
        indate = indate[0]

    # Indate can be a date without time...
    if not isinstance(indate, dt.datetime):
        try:
            indate = dt.datetime(indate.year, indate.month, indate.day, 0, 0, 0)
        except:
            _LOGGER.error("Unable to parse indate")

    # Indate can be TZ naive
    if indate.tzinfo is None or indate.tzinfo.utcoffset(indate) is None:
        _LOGGER.debug("TZ-Naive indate:")
        _LOGGER.debug(" < " + str(indate))
        tz = pytz.timezone(str(timezone))
        _LOGGER.debug("Add TZ:")
        _LOGGER.debug(tz)
        indate = tz.localize(indate)
        _LOGGER.debug(" > " + str(indate))
    return indate



def dateparser(calendar, date):
    """
    Takes a calendar and a date, and returns a sorted list
    of events on or after that date.
    """
    import arrow
    events = []


    # Ensure "now" is TZ-aware
    now = date.datetime
    dt_local_tz = dt.datetime.now().astimezone().tzinfo
    # pytz does not lke "CEST". But since it handles DST fine, we just use CET 
    local_tz = dt_local_tz
    if str(local_tz) == 'CEST':
        local_tz = 'CET'
    default_tz = pytz.timezone(str(local_tz))
    utc_tz = pytz.utc
    _LOGGER.debug("NOW: " + str(now))
    _LOGGER.debug("Default timezone: " + str(default_tz))

    for event in calendar.walk('VEVENT'):
        # RRULEs turns out to be harder than initially thought.  
        # This is maiiony due to pythons handling of TZ-naive and TZ-aware timestamps, and the inconsistensies 
        # in the way RRULEs are implemented in the icalendar library.  
        if 'RRULE' in event:
            _LOGGER.debug("RRULE in event: " + str(event['SUMMARY']))
            rrule = event['RRULE']
            # Since we dont get both the start and the end in a single object, we need to generate two lists,
            # One of all the DTSTARTs and another list of all the DTENDs
            start_rules = rruleset()
            end_rules = rruleset()

            if 'UNTIL' in rrule:
                _LOGGER.debug("UNTIL in rrule")
                until = datefixer(rrule['UNTIL'], 'UTC')
                rrule['UNTIL'] = [until]
            else:
                _LOGGER.debug("No UNTIL in rrule")

            # Lets try to generate a list of all DTSTARTs.  
            _LOGGER.debug("DTSTART in rrule")
            dtstart = datefixer(event['DTSTART'].dt, local_tz)
#            # Convert to datetime if needed
#            if not isinstance(dtstart, dt.datetime):
#                dtstart = dt.datetime(dtstart.year, dtstart.month, dtstart.day, 0, 0, 0)
#
#            # If the dtstart is tz-naive, we will add the local timezone 
#            # https://icalevents.com/2064-ical-local-or-floating-date-times/
#            if dtstart.tzinfo is None or dtstart.tzinfo.utcoffset(dtstart) is None:
#                _LOGGER.debug("TZ-Naive DTSTART:")
#                _LOGGER.debug(" < " + str(dtstart))
#                # Try to add default TZ
#                dtstart = default_tz.localize(dtstart)
#                _LOGGER.debug(" > " + str(dtstart))
#

            # And the same dance fot DTEND
            # If we don't have a DTEND, just use DTSTART
            if 'DTEND' not in event:
                dtend = dtstart
            else:
                _LOGGER.debug("DTEND in rrule")
                dtend = datefixer(event['DTEND'].dt, local_tz)
#                if not isinstance(dtend, dt.datetime):
#                    dtend = dt.datetime(dtend.year, dtend.month, dtend.day, 0, 0, 0)
#                if dtend.tzinfo is None or dtend.tzinfo.utcoffset(dtend) is None:
#                    dtend = default_tz.localize(dtend) 

            # So hopefully we now have a proper dtstart we can use to create the start-times according to the rrule
            try:
                start_rules.rrule(rrulestr(rrule.to_ical().decode("utf-8"), dtstart = dtstart))
            except Exception as e:
                # If this fails, move on to the next event
                _LOGGER.error("Exception in start_rules.rrule:")
                _LOGGER.error(e)
                _LOGGER.error(" - " + str(event['SUMMARY']))
                _LOGGER.error(" - " + str(dtstart))
                _LOGGER.error(" - " + str(event['RRULE']))
                continue

            try:
                end_rules.rrule(rrulestr(rrule.to_ical().decode("utf-8"), dtstart = dtend))
            except Exception as e:
                # If this fails, just use the start-rules
                _LOGGER.error("Exception in end_rules.rrule:")
                _LOGGER.error(e)
                _LOGGER.error(" - " + str(event['SUMMARY']))
                _LOGGER.error(" - " + str(dtend))
                _LOGGER.error(" - " + str(event['RRULE']))
                end_rules = start_rules

            # EXDATEs are hard to parse.  They might be a list, or just a single object.
            # They might contain TZ-data, they might not...
            # We just do our best, and will catch the exeption when it fails and move on the the next event.
            try:
                if 'EXDATE' in event:
                    if isinstance(event['EXDATE'], list):
                        for exdate in event['EXDATE']:
                            for edate in exdate.dts:
                                start_rules.exdate(edate.dt)
                                end_rules.exdate(edate.dt)
                    else:
                        for edate in event['EXDATE'].dts:
                            start_rules.exdate(edate.dt)
                            end_rules.exdate(edate.dt)
            except Exception as e:
                _LOGGER.error("Exception in EXDATE:")
                _LOGGER.error(e)
                _LOGGER.error(" - " + str(event['SUMMARY']))
                _LOGGER.error(" - " + str(event['RRULE']))
                _LOGGER.error(" - " + str(dtstart))
                _LOGGER.error(" - " + str(event['EXDATE']))
                continue

            # Lets get all RRULE-generated events which will start 7 days before today and end 30 days after today
            # to ensure we are catching recurring events that might already have started.
            try:
                starts = start_rules.between(after=(now - timedelta(days=7)), before=(now + timedelta(days=30)))
                ends = end_rules.between(after=(now - timedelta(days=7)), before=(now + timedelta(days=30)))
            except Exception as e:
                _LOGGER.error("Exception in starts/ends:")
                _LOGGER.error(e)
                _LOGGER.error(" - " + str(event['SUMMARY']))
                _LOGGER.error(" - " + str(event['RRULE']))
                _LOGGER.error(" - " + str(dtstart))
                _LOGGER.error(" - " + str(dtend))
                continue

            # We might get RRULEs that does not fall within the limits above, lets just skip them
            if len(starts) < 1:
                _LOGGER.debug("Event does not happen within our limits")
                continue

            # It has to be a better way to do this...But at least it seems to work for now.
            ends.reverse()
            for starte in starts:
                # Sometimes we dont get the same number of starts and ends...
                if len(ends) == 0:
                    continue
                end = arrow.get(str(ends.pop()))
                if end.date() < date.date():
                    _LOGGER.debug("This event has already ended")
                    continue
                start = arrow.get(str(starte))
                _LOGGER.debug("Event " + str(event['SUMMARY']) + " - possible start: " + str(start))


                # We should now have both a start and end arrow for the same event
                event_dict = {
                    'name': event['SUMMARY'],
                    'start': start.astimezone(dt_local_tz),
                    'end': end.astimezone(dt_local_tz)
                }

                # Add location if present
                if 'LOCATION' in event:
                    event_dict['location'] = event['LOCATION']

                _LOGGER.debug("Event to add:")
                _LOGGER.debug(event_dict)
                events.append(event_dict)

            _LOGGER.debug("Done parsing RRULE")

        else:
            # Let's use the same magic as for rrules to get this (as) right (as possible)
            _LOGGER.debug("DTSTART in rrule")
            dtstart = datefixer(event['DTSTART'].dt, local_tz)
            # dtstart = event['DTSTART'].dt
            # if not isinstance(dtstart, dt.datetime):
            #    dtstart = dt.datetime(dtstart.year, dtstart.month, dtstart.day, 0, 0, 0)

            # if dtstart.tzinfo is None or dtstart.tzinfo.utcoffset(dtstart) is None:
            #     dtstart = default_tz.localize(dtstart)
            start = arrow.get(dtstart)

            if 'DTEND' not in event:
                dtend = dtstart
            else:
                _LOGGER.debug("DTEND in rrule")
                dtend = datefixer(event['DTEND'].dt, local_tz)
                # dtend = event['DTEND'].dt
                # if not isinstance(dtend, dt.datetime):
                #     dtend = dt.datetime(dtend.year, dtend.month, dtend.day, 0, 0, 0)
                # if dtend.tzinfo is None or dtend.tzinfo.utcoffset(dtend) is None:
                #    dtend = default_tz.localize(dtend)
            end = arrow.get(dtend)

            # if isinstance(event['DTSTART'].dt, dt.date):
            #     start = arrow.get(str(event['DTSTART'].dt))
            # else:
            #     start = event['DTSTART'].dt

            # Add the end info if present.
            # if 'DTEND' in event:
            #     if isinstance(event['DTEND'].dt, dt.date):
            #         end = arrow.get(str(event['DTEND'].dt))
            #     else:
            #         end = event['DTEND'].dt
            # else:
            #    # Use "start" as end if no end is set
            #     end = start

            # Skip this event if it's in the past
            if end.date() < date.date():
                continue

            event_dict = {
                'name': event['SUMMARY'],
                'start': start.astimezone(dt_local_tz),
                'end': end.astimezone(dt_local_tz)
            }

            # Add location if present
            if 'LOCATION' in event:
                event_dict['location'] = event['LOCATION']

            events.append(event_dict)

    sorted_events = sorted(events, key=lambda k: k['start'])
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
            'location': None,
            'start': None,
            'end': None,
            'eta': None
        }
        # Get the data
        self.data_object.update()

        event_list = self.data_object.data
        if event_list and (self._eventno < len(event_list)):
            val = event_list[self._eventno]
            _LOGGER.debug("Adding event " + val.get('name', 'unknown') + " to calendar")
            _LOGGER.debug("- Start:")
            _LOGGER.debug(val['start'])
            start = val['start']
            self._event_attributes['start'] = start
            end = val['end']
            self._event_attributes['end'] = end
            location = val.get('location', '')
            self._event_attributes['location'] = location
            name = val.get('name', 'unknown')
            self._event_attributes['name'] = name
            self._event_attributes['eta'] = (start - dt.datetime.now(start.tzinfo) + timedelta(days=1)).days
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
                response = sess.send(self._request, timeout=30)

            cal = icalendar.Calendar.from_ical(response.text.replace("\x00", ""))
            today = arrow.utcnow()
            events = dateparser(cal, today)

            self.data = events

        except requests.exceptions.RequestException as e:
            _LOGGER.error("Error fetching data: %s", self._request)
            _LOGGER.error(e)
            self.data = None
