"""Fixtures for iCal integration tests."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from custom_components.ical import ICalEvents


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.async_add_executor_job = AsyncMock()
    return hass


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    config_entry = MagicMock(spec=ConfigEntry)
    config_entry.data = {
        "name": "test_calendar",
        "url": "file:///test/basic.ics",
        "max_events": 5,
        "days": 365,
        "verify_ssl": True
    }
    return config_entry


@pytest.fixture
def ical_events(mock_hass, mock_config_entry):
    """Create ICalEvents instance."""
    return ICalEvents(hass=mock_hass, config=mock_config_entry.data)


@pytest.fixture
def sample_ical_content():
    """Sample iCal content for testing."""
    return """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test Calendar//EN
BEGIN:VEVENT
UID:test1@test.com
DTSTART:20230101T120000Z
DTEND:20230101T130000Z
SUMMARY:Test Event 1
DESCRIPTION:This is a test event
LOCATION:Test Location
END:VEVENT
END:VCALENDAR"""


@pytest.fixture
def hass():
    """Mock Home Assistant instance for config flow tests."""
    return MagicMock(spec=HomeAssistant)
