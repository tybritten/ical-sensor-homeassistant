"""Tests for the ICalEvents class."""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from custom_components.ical import ICalEvents, check_event


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
        "verify_ssl": True,
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
    ical_events._ical_parser = AsyncMock(
        return_value=[
            {
                "summary": "Test Event 1",
                "start": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "end": datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
                "location": "Test Location",
                "description": "This is a test event",
                "all_day": False,
            }
        ]
    )

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

    ical_events.calendar = [
        {
            "summary": "Test Event 1",
            "start": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "end": datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            "location": "Test Location",
            "description": "This is a test event",
            "all_day": False,
        }
    ]

    # Mock the CalendarEvent class to avoid timezone validation issues
    with patch("custom_components.ical.CalendarEvent") as mock_calendar_event:
        mock_event_instance = MagicMock()
        mock_calendar_event.return_value = mock_event_instance

        events = await ical_events.async_get_events(mock_hass, start_date, end_date)

        assert len(events) == 1
        mock_calendar_event.assert_called_once_with(
            datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            "Test Event 1",
            "This is a test event",
            "Test Location",
        )


@pytest.mark.asyncio
async def test_ical_event_dict_with_past_event(mock_hass, basic_config):
    """Test _ical_event_dict includes past events (for calendar entity)."""
    ical_events = ICalEvents(hass=mock_hass, config=basic_config)

    from_date = datetime(2023, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    start = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    end = datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

    # Create a mock event
    event = MagicMock()
    event.get.return_value = "Past Event"

    with patch("homeassistant.util.dt.DEFAULT_TIME_ZONE", timezone.utc):
        result = ical_events._ical_event_dict(start, end, from_date, event)

    # Past events should be included (filtered later by sensors, not here)
    assert result is not None
    assert result["summary"] == "Past Event"


@pytest.mark.asyncio
async def test_ical_event_dict_with_future_event(mock_hass, basic_config):
    """Test _ical_event_dict with future event."""
    ical_events = ICalEvents(hass=mock_hass, config=basic_config)

    from_date = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    start = datetime(2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    end = datetime(2023, 1, 2, 13, 0, 0, tzinfo=timezone.utc)

    # Create a mock event
    event = MagicMock()
    event.get = MagicMock(
        side_effect=lambda key, default=None: {
            "SUMMARY": "Future Event",
            "LOCATION": "Test Location",
            "DESCRIPTION": "This is a future event",
        }.get(key, default)
    )

    with patch("homeassistant.util.dt.DEFAULT_TIME_ZONE", timezone.utc):
        result = ical_events._ical_event_dict(start, end, from_date, event)

        assert result is not None
        assert result["summary"] == "Future Event"
        assert result["location"] == "Test Location"
        assert result["description"] == "This is a future event"
        # The start time should be timezone-aware
        assert result["start"].tzinfo is not None
        assert result["end"].tzinfo is not None


def test_check_event_with_regular_event():
    """Test check_event returns datetime for non-all-day events."""
    dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = check_event(dt, all_day=False)
    assert isinstance(result, datetime)
    assert result == dt


def test_check_event_with_all_day_event():
    """Test check_event returns date for all-day events."""
    dt = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    result = check_event(dt, all_day=True)
    assert isinstance(result, date)
    assert not isinstance(result, datetime)
    assert result == date(2023, 1, 1)


@pytest.mark.asyncio
async def test_ical_event_dict_with_overnight_event(mock_hass, basic_config):
    """Test _ical_event_dict skips events where end <= start (issue #160)."""
    ical_events = ICalEvents(hass=mock_hass, config=basic_config)

    from_date = datetime(2023, 9, 4, 0, 0, 0, tzinfo=timezone.utc)
    # Overnight event where TZ conversion made end appear before start
    start = datetime(2023, 9, 4, 22, 0, 0, tzinfo=timezone.utc)
    end = datetime(2023, 9, 4, 6, 0, 0, tzinfo=timezone.utc)

    event = MagicMock()
    event.get = MagicMock(return_value="Overnight Event")

    result = ical_events._ical_event_dict(start, end, from_date, event)

    # Should return None because end is before start
    assert result is None


@pytest.mark.asyncio
async def test_ical_event_dict_with_zero_duration_event(mock_hass, basic_config):
    """Test _ical_event_dict allows zero-duration events (end == start)."""
    ical_events = ICalEvents(hass=mock_hass, config=basic_config)

    from_date = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    start = datetime(2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    end = datetime(2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

    event = MagicMock()
    event.get = MagicMock(return_value="Zero Duration Event")

    with patch("homeassistant.util.dt.DEFAULT_TIME_ZONE", timezone.utc):
        result = ical_events._ical_event_dict(start, end, from_date, event)

    # Zero-duration events should be allowed (end == start is OK)
    assert result is not None
    assert result["summary"] == "Zero Duration Event"


@pytest.mark.asyncio
async def test_async_get_events_all_day(mock_hass, basic_config):
    """Test async_get_events passes date objects for all-day events."""
    ical_events = ICalEvents(hass=mock_hass, config=basic_config)

    start_date = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_date = datetime(2023, 1, 3, 0, 0, 0, tzinfo=timezone.utc)

    ical_events.calendar = [
        {
            "summary": "All Day Event",
            "start": datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "end": datetime(2023, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
            "location": None,
            "description": None,
            "all_day": True,
        }
    ]

    with patch("custom_components.ical.CalendarEvent") as mock_calendar_event:
        mock_calendar_event.return_value = MagicMock()

        events = await ical_events.async_get_events(mock_hass, start_date, end_date)

        assert len(events) == 1
        # check_event should convert to date objects for all-day events
        call_args = mock_calendar_event.call_args[0]
        assert isinstance(call_args[0], date)
        assert not isinstance(call_args[0], datetime)
        assert isinstance(call_args[1], date)
        assert not isinstance(call_args[1], datetime)


@pytest.mark.asyncio
async def test_ical_event_dict_all_day_event(mock_hass, basic_config):
    """Test all-day events with midnight start/end are handled correctly."""
    ical_events = ICalEvents(hass=mock_hass, config=basic_config)
    ical_events.all_day = True

    # All-day event: start and end are both midnight on the same day
    from_date = datetime(2023, 6, 24, 0, 0, 0, tzinfo=timezone.utc)
    start = datetime(2023, 6, 24, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2023, 6, 24, 0, 0, 0, tzinfo=timezone.utc)

    event = MagicMock()
    event.get = MagicMock(return_value="All Day Event")

    with patch("homeassistant.util.dt.DEFAULT_TIME_ZONE", timezone.utc):
        result = ical_events._ical_event_dict(start, end, from_date, event)

    assert result is not None
    assert result["summary"] == "All Day Event"
