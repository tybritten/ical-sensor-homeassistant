"""Tests for the ICalEvents class."""
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from icalendar import Calendar
import pytz

from custom_components.ical import ICalEvents
from homeassistant.util import dt as dt_util
from homeassistant.components.calendar import CalendarEvent


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock()
    return hass


@pytest.fixture
def basic_config():
    """Basic configuration for testing."""
    return {
        "name": "test_calendar",
        "url": "file:///test/basic.ics",
        "max_events": 5,
        "days": 365,
        "verify_ssl": True
    }


def test_ical_events_init(mock_hass, basic_config):
    """Test ICalEvents initialization."""
    ical_events = ICalEvents(hass=mock_hass, config=basic_config)
    
    assert ical_events.hass == mock_hass
    assert ical_events.name == "test_calendar"
    assert ical_events.url == "file:///test/basic.ics"
    assert ical_events.max_events == 5
    assert ical_events.days == 365
    assert ical_events.verify_ssl is True
    assert ical_events.calendar == []
    assert ical_events.event is None
    assert ical_events.all_day is False


@pytest.mark.asyncio
async def test_ical_date_fixer_with_datetime(mock_hass, basic_config):
    """Test _ical_date_fixer with datetime object."""
    ical_events = ICalEvents(hass=mock_hass, config=basic_config)
    
    # Mock the hass.async_add_executor_job to return the datetime as-is
    mock_hass.async_add_executor_job = AsyncMock(side_effect=lambda f, *args: f(*args))
    
    test_date = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = await ical_events._ical_date_fixer(test_date, "UTC")
    
    assert isinstance(result, datetime)
    assert result.year == 2023
    assert result.month == 1
    assert result.day == 1
    assert result.hour == 12


@pytest.mark.asyncio
async def test_ical_date_fixer_with_date(mock_hass, basic_config):
    """Test _ical_date_fixer with date object."""
    ical_events = ICalEvents(hass=mock_hass, config=basic_config)
    
    from datetime import date
    test_date = date(2023, 1, 1)
    
    # Mock the hass.async_add_executor_job to return a datetime
    mock_hass.async_add_executor_job = AsyncMock(
        side_effect=lambda f, *args: datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    )
    
    result = await ical_events._ical_date_fixer(test_date, "UTC")
    
    assert isinstance(result, datetime)
    assert result.year == 2023
    assert result.month == 1
    assert result.day == 1
    assert ical_events.all_day is True


@pytest.mark.asyncio
async def test_update_with_file_url(mock_hass, basic_config, tmp_path):
    """Test update method with file URL."""
    # Create a temporary ics file
    ics_content = """BEGIN:VCALENDAR
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
    
    ics_file = tmp_path / "test.ics"
    ics_file.write_text(ics_content)
    
    # Update config to use the temporary file
    file_config = basic_config.copy()
    file_config["url"] = f"file://{ics_file}"
    
    ical_events = ICalEvents(hass=mock_hass, config=file_config)
    
    # Mock the _ical_parser to return a simple event
    ical_events._ical_parser = AsyncMock(return_value=[{
        "summary": "Test Event 1",
        "start": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        "end": datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        "location": "Test Location",
        "description": "This is a test event",
        "all_day": False
    }])
    
    await ical_events.update()
    
    # Verify that the calendar was updated
    assert len(ical_events.calendar) == 1
    assert ical_events.calendar[0]["summary"] == "Test Event 1"


@pytest.mark.asyncio
async def test_async_get_events(mock_hass, basic_config):
    """Test async_get_events method."""
    ical_events = ICalEvents(hass=mock_hass, config=basic_config)
    
    # Set up some test events
    start_date = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_date = datetime(2023, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    
    ical_events.calendar = [{
        "summary": "Test Event 1",
        "start": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        "end": datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        "location": "Test Location",
        "description": "This is a test event",
        "all_day": False
    }]
    
    # Mock the CalendarEvent class to avoid timezone validation issues
    with patch('custom_components.ical.CalendarEvent') as mock_calendar_event:
        mock_event_instance = MagicMock()
        mock_calendar_event.return_value = mock_event_instance
        
        events = await ical_events.async_get_events(mock_hass, start_date, end_date)
        
        assert len(events) == 1
        mock_calendar_event.assert_called_once_with(
            datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            "Test Event 1",
            "This is a test event",
            "Test Location"
        )


@pytest.mark.asyncio
async def test_ical_event_dict_with_past_event(mock_hass, basic_config):
    """Test _ical_event_dict with past event."""
    ical_events = ICalEvents(hass=mock_hass, config=basic_config)
    
    from_date = datetime(2023, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    start = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    end = datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
    
    # Create a mock event
    event = MagicMock()
    event.get.return_value = "Past Event"
    
    result = ical_events._ical_event_dict(start, end, from_date, event)
    
    # Should return None for past events
    assert result is None


@pytest.mark.asyncio
async def test_ical_event_dict_with_future_event(mock_hass, basic_config):
    """Test _ical_event_dict with future event."""
    ical_events = ICalEvents(hass=mock_hass, config=basic_config)
    
    from_date = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    start = datetime(2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    end = datetime(2023, 1, 2, 13, 0, 0, tzinfo=timezone.utc)
    
    # Create a mock event
    event = MagicMock()
    event.get = MagicMock(side_effect=lambda key, default=None: {
        "SUMMARY": "Future Event",
        "LOCATION": "Test Location",
        "DESCRIPTION": "This is a future event"
    }.get(key, default))
    
    with patch('homeassistant.util.dt.DEFAULT_TIME_ZONE', timezone.utc):
        result = ical_events._ical_event_dict(start, end, from_date, event)
    
        assert result is not None
        assert result["summary"] == "Future Event"
        assert result["location"] == "Test Location"
        assert result["description"] == "This is a future event"
        # The start time should be timezone-aware
        assert result["start"].tzinfo is not None
        assert result["end"].tzinfo is not None
