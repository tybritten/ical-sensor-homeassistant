"""Tests for the sensor platform."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from custom_components.ical.sensor import ICalSensor


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    return MagicMock()


@pytest.fixture
def mock_ical_events():
    """Mock ICalEvents instance."""
    ical_events = MagicMock()
    ical_events.name = "test_calendar"
    ical_events.update = AsyncMock()
    ical_events.calendar = [
        {
            "summary": "Test Event 1",
            "start": datetime(2023, 1, 1, 12, 0, 0),
            "end": datetime(2023, 1, 1, 13, 0, 0),
            "location": "Test Location 1",
            "description": "Test Description 1",
            "all_day": False,
        },
        {
            "summary": "Test Event 2",
            "start": datetime(2023, 1, 2, 14, 0, 0),
            "end": datetime(2023, 1, 2, 15, 0, 0),
            "location": "Test Location 2",
            "description": "Test Description 2",
            "all_day": False,
        },
    ]
    return ical_events


def test_sensor_init(mock_hass, mock_ical_events):
    """Test ICalSensor initialization."""
    sensor = ICalSensor(
        hass=mock_hass,
        ical_events=mock_ical_events,
        sensor_name="test_calendar",
        event_number=0,
        entry_id="test_entry_id",
    )

    assert sensor._event_number == 0
    assert sensor._hass == mock_hass
    assert sensor.ical_events == mock_ical_events
    assert sensor._state is None
    assert sensor._is_available is None

    # Check that event attributes are initialized
    assert sensor._event_attributes["summary"] is None
    assert sensor._event_attributes["description"] is None
    assert sensor._event_attributes["location"] is None
    assert sensor._event_attributes["start"] is None
    assert sensor._event_attributes["end"] is None
    assert sensor._event_attributes["eta"] is None


def test_sensor_unique_id(mock_hass, mock_ical_events):
    """Test ICalSensor unique_id property."""
    sensor = ICalSensor(
        hass=mock_hass,
        ical_events=mock_ical_events,
        sensor_name="test_calendar",
        event_number=0,
        entry_id="test_entry_id",
    )

    assert sensor.unique_id == "test_entry_id_event_0"


def test_sensor_name(mock_hass, mock_ical_events):
    """Test ICalSensor name property."""
    sensor = ICalSensor(
        hass=mock_hass,
        ical_events=mock_ical_events,
        sensor_name="test_calendar",
        event_number=0,
        entry_id="test_entry_id",
    )

    # Name should be None initially since event attributes haven't been set
    assert sensor.name is None


def test_sensor_icon(mock_hass, mock_ical_events):
    """Test ICalSensor icon property."""
    from custom_components.ical.const import ICON

    sensor = ICalSensor(
        hass=mock_hass,
        ical_events=mock_ical_events,
        sensor_name="test_calendar",
        event_number=0,
        entry_id="test_entry_id",
    )

    assert sensor.icon == ICON


def test_sensor_state(mock_hass, mock_ical_events):
    """Test ICalSensor state property."""
    sensor = ICalSensor(
        hass=mock_hass,
        ical_events=mock_ical_events,
        sensor_name="test_calendar",
        event_number=0,
        entry_id="test_entry_id",
    )

    # State should be None initially
    assert sensor.state is None


def test_sensor_extra_state_attributes(mock_hass, mock_ical_events):
    """Test ICalSensor extra_state_attributes property."""
    sensor = ICalSensor(
        hass=mock_hass,
        ical_events=mock_ical_events,
        sensor_name="test_calendar",
        event_number=0,
        entry_id="test_entry_id",
    )

    # Should return the event attributes
    attrs = sensor.extra_state_attributes
    assert attrs["summary"] is None
    assert attrs["description"] is None
    assert attrs["location"] is None
    assert attrs["start"] is None
    assert attrs["end"] is None
    assert attrs["eta"] is None


def test_sensor_available(mock_hass, mock_ical_events):
    """Test ICalSensor available property."""
    sensor = ICalSensor(
        hass=mock_hass,
        ical_events=mock_ical_events,
        sensor_name="test_calendar",
        event_number=0,
        entry_id="test_entry_id",
    )

    # Should be False initially since start is None
    assert sensor.available is False


@pytest.mark.asyncio
async def test_sensor_async_update_with_event(mock_hass, mock_ical_events):
    """Test ICalSensor async_update method with event."""
    sensor = ICalSensor(
        hass=mock_hass,
        ical_events=mock_ical_events,
        sensor_name="test_calendar",
        event_number=0,
        entry_id="test_entry_id",
    )

    await sensor.async_update()

    # Verify that ical_events.update was called
    mock_ical_events.update.assert_called_once()

    # Verify that the state and attributes were updated
    assert sensor.state is not None
    assert sensor._event_attributes["summary"] == "Test Event 1"
    assert sensor._event_attributes["start"] == datetime(2023, 1, 1, 12, 0, 0)
    assert sensor._event_attributes["end"] == datetime(2023, 1, 1, 13, 0, 0)
    assert sensor._event_attributes["location"] == "Test Location 1"
    assert sensor._event_attributes["description"] == "Test Description 1"
    assert sensor.available is True


@pytest.mark.asyncio
async def test_sensor_async_update_with_no_more_events(mock_hass, mock_ical_events):
    """Test ICalSensor async_update method with no more events."""
    sensor = ICalSensor(
        hass=mock_hass,
        ical_events=mock_ical_events,
        sensor_name="test_calendar",
        event_number=5,  # This is beyond the number of events in the calendar
        entry_id="test_entry_id",
    )

    await sensor.async_update()

    # Verify that ical_events.update was called
    mock_ical_events.update.assert_called_once()

    # Verify that the state and attributes were reset
    assert sensor.state is None
    assert sensor._event_attributes["summary"] is None
    assert sensor._event_attributes["start"] is None
    assert sensor._event_attributes["end"] is None
    assert sensor._event_attributes["location"] is None
    assert sensor._event_attributes["description"] is None
    assert sensor._event_attributes["eta"] is None
    assert sensor.available is False


@pytest.mark.asyncio
async def test_sensor_async_update_with_all_day_event(mock_hass):
    """Test ICalSensor async_update method with all-day event."""
    # Create mock ical_events with an all-day event
    ical_events = MagicMock()
    ical_events.name = "test_calendar"
    ical_events.update = AsyncMock()
    ical_events.calendar = [
        {
            "summary": "All Day Event",
            "start": datetime(2023, 1, 1, 0, 0, 0),
            "end": datetime(2023, 1, 2, 0, 0, 0),
            "location": "Test Location",
            "description": "Test Description",
            "all_day": True,
        }
    ]

    sensor = ICalSensor(
        hass=mock_hass,
        ical_events=ical_events,
        sensor_name="test_calendar",
        event_number=0,
        entry_id="test_entry_id",
    )

    await sensor.async_update()

    # Verify the state format for all-day events
    assert sensor.state == "All Day Event - 1 January 2023"
