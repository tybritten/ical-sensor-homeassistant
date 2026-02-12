"""Creating sensors for upcoming events."""

from datetime import datetime, timedelta
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_MAX_EVENTS, DOMAIN, ICON

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the iCal Sensor."""
    config = config_entry.data
    name = config.get(CONF_NAME)
    max_events = config.get(CONF_MAX_EVENTS)

    ical_events = hass.data[DOMAIN][config_entry.entry_id]
    await ical_events.update()
    if ical_events.calendar is None:
        _LOGGER.error("Unable to fetch iCal")
        return False

    # Migrate old name-based unique_ids to entry_id-based
    ent_reg = er.async_get(hass)
    for eventnumber in range(max_events):
        old_uid = f"{name.lower()}_event_{eventnumber}"
        new_uid = f"{config_entry.entry_id}_event_{eventnumber}"
        if old_uid != new_uid:
            existing = ent_reg.async_get_entity_id("sensor", DOMAIN, old_uid)
            if existing is not None:
                ent_reg.async_update_entity(existing, new_unique_id=new_uid)

    sensors = []
    for eventnumber in range(max_events):
        sensors.append(
            ICalSensor(
                hass, ical_events, DOMAIN + " " + name, eventnumber,
                entry_id=config_entry.entry_id,
            )
        )

    async_add_entities(sensors)


# pylint: disable=too-few-public-methods
class ICalSensor(SensorEntity):
    """Implementation of a iCal sensor.

    Represents the Nth upcoming event.
    May have a name like 'sensor.mycalander_event_0' for the first
    upcoming event.
    """

    def __init__(
        self, hass: HomeAssistant, ical_events, sensor_name, event_number,
        *, entry_id: str,
    ) -> None:
        """Initialize the sensor.

        sensor_name is typically the name of the calendar.
        eventnumber indicates which upcoming event this is, starting at zero
        """
        super().__init__()
        self._event_number = event_number
        self._hass = hass
        self.ical_events = ical_events
        self._entry_id = entry_id
        self._event_attributes = {
            "summary": None,
            "description": None,
            "location": None,
            "start": None,
            "end": None,
            "eta": None,
        }
        self._state = None
        self._is_available = None

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{self._entry_id}_event_{self._event_number}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._event_attributes["summary"]

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return ICON

    @property
    def state(self):
        """Return the date of the next event."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the attributes of the event."""
        return self._event_attributes

    @property
    def available(self):
        """Return True if ZoneMinder is available."""
        return self.extra_state_attributes["start"] is not None

    async def async_update(self):
        """Update the sensor."""
        _LOGGER.debug("Running ICalSensor async update for %s", self.name)

        await self.ical_events.update()

        event_list = self.ical_events.calendar
        # _LOGGER.debug(f"Event List: {event_list}")
        if event_list and (self._event_number < len(event_list)):
            val = event_list[self._event_number]
            name = val.get("summary", "Unknown")
            start = val.get("start")

            # _LOGGER.debug(f"Val: {val}")
            _LOGGER.debug(
                "Adding event %s - Start %s - End %s - as event %s to calendar %s",
                val.get("summary", "unknown"),
                val.get("start"),
                val.get("end"),
                str(self._event_number),
                self.name,
            )

            self._event_attributes["summary"] = val.get("summary", "unknown")
            self._event_attributes["start"] = val.get("start")
            self._event_attributes["end"] = val.get("end")
            self._event_attributes["location"] = val.get("location", "")
            self._event_attributes["description"] = val.get("description", "")
            self._event_attributes["eta"] = (
                start - datetime.now(start.tzinfo) + timedelta(days=1)
            ).days
            self._event_attributes["all_day"] = val.get("all_day")
            self._state = f"{name} - {start.strftime('%-d %B %Y')}"
            if not val.get("all_day"):
                self._state += f" {start.strftime('%H:%M')}"
            # self._is_available = True
        elif self._event_number >= len(event_list):
            # No further events are found in the calendar
            self._event_attributes = {
                "summary": None,
                "description": None,
                "location": None,
                "start": None,
                "end": None,
                "eta": None,
            }
            self._state = None
            self._is_available = None
