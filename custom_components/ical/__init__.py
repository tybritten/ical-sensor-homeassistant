"""The ical integration."""

import asyncio
from datetime import date, datetime, timedelta
import logging
from urllib.parse import urlparse

import icalendar
import recurring_ical_events

from homeassistant.components.calendar import CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_URL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle, dt as dt_util

from .const import CONF_DAYS, CONF_MAX_EVENTS, DOMAIN

_LOGGER = logging.getLogger(__name__)


PLATFORMS = ["sensor", "calendar"]

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=120)


def check_event(d: datetime, all_day: bool) -> datetime | date:
    """Return date object for all-day events, datetime otherwise."""
    return d.date() if all_day else d


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up ical from a config entry."""
    config = entry.data
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = ICalEvents(hass=hass, config=config)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class ICalEvents:
    """Get a list of events."""

    def __init__(self, hass: HomeAssistant, config):
        """Set up a calendar object."""
        self.hass = hass
        self.name = config.get(CONF_NAME)
        self.url = config.get(CONF_URL)
        self.max_events = config.get(CONF_MAX_EVENTS)
        self.days = config.get(CONF_DAYS)
        self.verify_ssl = config.get(CONF_VERIFY_SSL)
        self.calendar = []
        self.event = None
        self.all_day = False

    async def async_get_events(self, hass: HomeAssistant, start_date, end_date):
        """Get list of upcoming events."""
        events = []
        if len(self.calendar) > 0:
            for event in self.calendar:

                if event["start"] < end_date and event["end"] > start_date:
                    events.append(
                        CalendarEvent(
                            check_event(event["start"], event["all_day"]),
                            check_event(event["end"], event["all_day"]),
                            event["summary"],
                            event["description"],
                            event["location"],
                        )
                    )
                    # events.append(event)
        return events

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def update(self):
        """Update list of upcoming events."""
        parts = urlparse(self.url)
        if parts.scheme == "file":
            with open(parts.path) as f:
                text = f.read()
        else:
            if parts.scheme == "webcal":
                self.url = parts.geturl().replace("webcal", "https", 1)
            session = async_get_clientsession(self.hass, verify_ssl=self.verify_ssl)
            async with session.get(self.url) as response:
                text = await response.text()
        if text is not None:
            loop = asyncio.get_running_loop()
            event_list = await loop.run_in_executor(
                None, icalendar.Calendar.from_ical, text.replace("\x00", "")
            )
            start_of_events = dt_util.start_of_local_day()
            end_of_events = dt_util.start_of_local_day() + timedelta(days=self.days)

            self.calendar = await self._ical_parser(
                event_list, start_of_events, end_of_events
            )

        if len(self.calendar) > 0:
            found_next_event = False
            for event in self.calendar:
                if event["end"] > dt_util.now() and not found_next_event:
                    self.event = event
                    found_next_event = True

    async def _ical_parser(self, calendar, from_date, to_date):
        """Return a sorted list of events from a icalendar object."""
        events = []

        recurring_events = await self.hass.async_add_executor_job(
            lambda: recurring_ical_events.of(calendar, skip_bad_series=True).between(
                from_date, to_date
            )
        )

        for event in recurring_events:
            dtstart = event["DTSTART"].dt
            dtend = event["DTEND"].dt if "DTEND" in event else dtstart

            # Detect all-day events (date objects, not datetime)
            self.all_day = isinstance(dtstart, date) and not isinstance(
                dtstart, datetime
            )

            # Convert date to datetime for consistent handling
            if not isinstance(dtstart, datetime):
                dtstart = datetime(
                    dtstart.year,
                    dtstart.month,
                    dtstart.day,
                    tzinfo=dt_util.DEFAULT_TIME_ZONE,
                )
            if not isinstance(dtend, datetime):
                dtend = datetime(
                    dtend.year,
                    dtend.month,
                    dtend.day,
                    tzinfo=dt_util.DEFAULT_TIME_ZONE,
                )

            # Ensure timezone awareness
            if dtstart.tzinfo is None:
                dtstart = dtstart.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
            if dtend.tzinfo is None:
                dtend = dtend.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)

            event_dict = self._ical_event_dict(dtstart, dtend, from_date, event)
            if event_dict:
                events.append(event_dict)

        return sorted(events, key=lambda k: k["start"])

    def _ical_event_dict(self, start, end, from_date, event):
        """Ensure that events are within the start and end."""

        # Skip events where end is before start (can happen with
        # overnight events after timezone conversion, see issue #160)
        if end < start:
            _LOGGER.warning(
                "Skipping event '%s': end (%s) is before start (%s)",
                event.get("SUMMARY", "Unknown"),
                end,
                start,
            )
            return None

        # Skip this event if it's in the past
        if end.date() < from_date.date():
            # Only log if we're at debug level to avoid performance impact
            if _LOGGER.isEnabledFor(logging.DEBUG):
                _LOGGER.debug("This event has already ended")
            return None
        # Ignore events that ended this midnight.
        if (
            end.date() == from_date.date()
            and end.hour == 0
            and end.minute == 0
            and end.second == 0
        ):
            # Only log if we're at debug level to avoid performance impact
            if _LOGGER.isEnabledFor(logging.DEBUG):
                _LOGGER.debug("This event has already ended")
            return None
        # Only log if we're at debug level to avoid performance impact
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug(
                "Start: %s Tzinfo: %s Default: %s StartAs %s",
                str(start),
                str(start.tzinfo),
                dt_util.DEFAULT_TIME_ZONE,
                start.astimezone(dt_util.DEFAULT_TIME_ZONE),
            )
        event_dict = {
            "summary": event.get("SUMMARY", "Unknown"),
            "start": start.astimezone(dt_util.DEFAULT_TIME_ZONE),
            "end": end.astimezone(dt_util.DEFAULT_TIME_ZONE),
            "location": event.get("LOCATION"),
            "description": event.get("DESCRIPTION"),
            "all_day": self.all_day,
        }
        # Only log if we're at debug level to avoid performance impact
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("Event to add: %s", str(event_dict))
        return event_dict
