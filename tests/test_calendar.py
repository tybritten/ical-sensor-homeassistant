"""Tests for the calendar platform."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from homeassistant.components.calendar import CalendarEvent
from pathlib import Path

from custom_components.ical.calendar import ICalCalendarEventDevice


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    return MagicMock()


@pytest.fixture
def mock_ical_events():
    """Mock ICalEvents instance."""
    ical_events = MagicMock()
    ical_events.event = {
        "summary": "Test Event",
        "start": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        "end": datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        "location": "Test Location",
        "description": "Test Description",
        "all_day": False
    }
    ical_events.async_get_events = AsyncMock(return_value=[])
    ical_events.update = AsyncMock()
    return ical_events


def test_calendar_device_init(mock_hass, mock_ical_events):
    """Test ICalCalendarEventDevice initialization."""
    device = ICalCalendarEventDevice(
        hass=mock_hass,
        name="test_calendar",
        entity_id="calendar.test_calendar",
        ical_events=mock_ical_events
    )
    
    assert device.entity_id == "calendar.test_calendar"
    assert device._name == "test_calendar"
    assert device.ical_events == mock_ical_events
    assert device._event is None
    assert device._offset_reached is False


def test_calendar_device_name(mock_hass, mock_ical_events):
    """Test ICalCalendarEventDevice name property."""
    device = ICalCalendarEventDevice(
        hass=mock_hass,
        name="test_calendar",
        entity_id="calendar.test_calendar",
        ical_events=mock_ical_events
    )
    
    assert device.name == "test_calendar"


def test_calendar_device_event(mock_hass, mock_ical_events):
    """Test ICalCalendarEventDevice event property."""
    device = ICalCalendarEventDevice(
        hass=mock_hass,
        name="test_calendar",
        entity_id="calendar.test_calendar",
        ical_events=mock_ical_events
    )
    
    # Initially should be None
    assert device.event is None
    
    # Set an event and test
    test_event = CalendarEvent(
        start=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        end=datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        summary="Test Event"
    )
    device._event = test_event
    
    assert device.event == test_event


def test_calendar_device_extra_state_attributes(mock_hass, mock_ical_events):
    """Test ICalCalendarEventDevice extra_state_attributes property."""
    device = ICalCalendarEventDevice(
        hass=mock_hass,
        name="test_calendar",
        entity_id="calendar.test_calendar",
        ical_events=mock_ical_events
    )
    
    # Test with offset not reached
    device._offset_reached = False
    attrs = device.extra_state_attributes
    assert attrs["offset_reached"] is False
    
    # Test with offset reached
    device._offset_reached = True
    attrs = device.extra_state_attributes
    assert attrs["offset_reached"] is True


@pytest.mark.asyncio
async def test_calendar_device_async_get_events(mock_hass, mock_ical_events):
    """Test ICalCalendarEventDevice async_get_events method."""
    device = ICalCalendarEventDevice(
        hass=mock_hass,
        name="test_calendar",
        entity_id="calendar.test_calendar",
        ical_events=mock_ical_events
    )
    
    start_date = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_date = datetime(2023, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    
    # Mock the ical_events.async_get_events to return test events
    test_events = [
        CalendarEvent(
            start=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            end=datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            summary="Test Event"
        )
    ]
    mock_ical_events.async_get_events.return_value = test_events
    
    events = await device.async_get_events(mock_hass, start_date, end_date)
    
    assert len(events) == 1
    assert events[0].summary == "Test Event"
    mock_ical_events.async_get_events.assert_called_once_with(mock_hass, start_date, end_date)


@pytest.mark.asyncio
async def test_calendar_device_async_update(mock_hass, mock_ical_events):
    """Test ICalCalendarEventDevice async_update method."""
    device = ICalCalendarEventDevice(
        hass=mock_hass,
        name="test_calendar",
        entity_id="calendar.test_calendar",
        ical_events=mock_ical_events
    )
    
    # Mock the copy.deepcopy to return the same event
    with patch('copy.deepcopy', side_effect=lambda x: x):
        await device.async_update()
    
    # Verify that ical_events.update was called
    mock_ical_events.update.assert_called_once()
    
    # Verify that the event was set
    assert device._event is not None
    assert device._event.summary == "Test Event"


@pytest.mark.asyncio
async def test_calendar_device_async_update_with_no_event(mock_hass):
    """Test ICalCalendarEventDevice async_update method with no event."""
    # Create a mock ical_events with no event
    ical_events = MagicMock()
    ical_events.event = None
    ical_events.update = AsyncMock()
    
    device = ICalCalendarEventDevice(
        hass=mock_hass,
        name="test_calendar",
        entity_id="calendar.test_calendar",
        ical_events=ical_events
    )
    
    await device.async_update()
    
    # Verify that ical_events.update was called
    ical_events.update.assert_called_once()
    
    # Verify that the event is None
    assert device._event is None


@pytest.mark.asyncio
async def test_calendar_device_with_rrule_ics_file(mock_hass):
    """Test ICalCalendarEventDevice with the rrule.ics file that currently causes errors."""
    # This test demonstrates the error condition with the rrule.ics file
    # The error is logged but not raised as an exception
    
    # Get the path to the rrule.ics file
    rrule_file_path = Path(__file__).parent / "fixtures" / "sample_calendars" / "rrule.ics"
    
    # Create config that points to the rrule.ics file
    config = {
        "name": "test_rrule_calendar",
        "url": f"file://{rrule_file_path}",
        "max_events": 5,
        "days": 30,
        "verify_ssl": True
    }
    
    # Create ICalEvents instance with the config
    from custom_components.ical import ICalEvents
    ical_events = ICalEvents(hass=mock_hass, config=config)
    
    # Mock the hass.async_add_executor_job to avoid actual file I/O in tests
    mock_hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))
    
    # Mock logging to capture error messages
    with patch('custom_components.ical._LOGGER.error') as mock_error:
        await ical_events.update()
        
        # Check that the specific error was logged
        error_logged = any(
            "'<' not supported between instances of 'datetime.date' and 'datetime.datetime'" in str(call)
            for call in mock_error.call_args_list
        )
        
        # Assert that the error was logged
        assert error_logged, "Expected error was not logged"
        
        # Note: Some events may still be processed despite the error
        # The important thing is that the error is logged
