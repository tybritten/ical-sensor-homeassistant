"""Test utilities for iCal component tests."""

from datetime import datetime
import os
from typing import Dict, List, Optional


def generate_basic_ical_event(
    uid: str = "test1@example.com",
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    summary: str = "Test Event",
    description: str = "This is a test event",
    location: str = "Test Location",
) -> str:
    """Generate a basic iCal event as a string."""
    if start is None:
        start = datetime(2023, 1, 1, 12, 0, 0)
    if end is None:
        end = datetime(2023, 1, 1, 13, 0, 0)

    # Format dates in iCal format
    start_str = start.strftime("%Y%m%dT%H%M%SZ")
    end_str = end.strftime("%Y%m%dT%H%M%SZ")

    return f"""BEGIN:VEVENT
UID:{uid}
DTSTART:{start_str}
DTEND:{end_str}
SUMMARY:{summary}
DESCRIPTION:{description}
LOCATION:{location}
END:VEVENT"""


def generate_recurring_ical_event(
    uid: str = "recurring1@example.com",
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    summary: str = "Recurring Event",
    rrule: str = "FREQ=DAILY;COUNT=5",
) -> str:
    """Generate a recurring iCal event as a string."""
    if start is None:
        start = datetime(2023, 1, 1, 12, 0, 0)
    if end is None:
        end = datetime(2023, 1, 1, 13, 0, 0)

    # Format dates in iCal format
    start_str = start.strftime("%Y%m%dT%H%M%SZ")
    end_str = end.strftime("%Y%m%dT%H%M%SZ")

    return f"""BEGIN:VEVENT
UID:{uid}
DTSTART:{start_str}
DTEND:{end_str}
SUMMARY:{summary}
RRULE:{rrule}
END:VEVENT"""


def generate_all_day_ical_event(
    uid: str = "allday1@example.com",
    date: Optional[datetime] = None,
    summary: str = "All Day Event",
) -> str:
    """Generate an all-day iCal event as a string."""
    if date is None:
        date = datetime(2023, 1, 1)

    # Format date in iCal format (no time component)
    date_str = date.strftime("%Y%m%d")

    return f"""BEGIN:VEVENT
UID:{uid}
DTSTART;VALUE=DATE:{date_str}
DTEND;VALUE=DATE:{date_str}
SUMMARY:{summary}
END:VEVENT"""


def generate_timezone_ical_event(
    uid: str = "timezone1@example.com",
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    summary: str = "Timezone Event",
    timezone: str = "America/New_York",
) -> str:
    """Generate a timezone-aware iCal event as a string."""
    if start is None:
        start = datetime(2023, 1, 1, 12, 0, 0)
    if end is None:
        end = datetime(2023, 1, 1, 13, 0, 0)

    # Format dates in iCal format with timezone
    start_str = start.strftime("%Y%m%dT%H%M%S")
    end_str = end.strftime("%Y%m%dT%H%M%S")

    return f"""BEGIN:VEVENT
UID:{uid}
DTSTART;TZID={timezone}:{start_str}
DTEND;TZID={timezone}:{end_str}
SUMMARY:{summary}
END:VEVENT"""


def create_test_ical_calendar(events: List[str]) -> str:
    """Create a complete iCal calendar from a list of events."""
    events_str = "\n".join(events)
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test Calendar//EN
{events_str}
END:VCALENDAR"""


def create_sample_ical_files(base_path: str) -> Dict[str, str]:
    """Create sample iCal files for testing and return their paths.

    Args:
        base_path: Directory where files should be created

    Returns:
        Dictionary mapping file names to their full paths
    """
    # Ensure the directory exists
    os.makedirs(base_path, exist_ok=True)

    files = {}

    # Create basic.ics
    basic_events = [
        generate_basic_ical_event(
            uid="basic1@example.com",
            start=datetime(2023, 1, 1, 12, 0, 0),
            end=datetime(2023, 1, 1, 13, 0, 0),
            summary="Basic Event 1",
        ),
        generate_basic_ical_event(
            uid="basic2@example.com",
            start=datetime(2023, 1, 2, 14, 0, 0),
            end=datetime(2023, 1, 2, 15, 0, 0),
            summary="Basic Event 2",
        ),
    ]
    basic_calendar = create_test_ical_calendar(basic_events)
    basic_path = os.path.join(base_path, "basic.ics")
    with open(basic_path, "w") as f:
        f.write(basic_calendar)
    files["basic"] = basic_path

    # Create recurring.ics
    recurring_events = [
        generate_recurring_ical_event(
            uid="recurring1@example.com",
            start=datetime(2023, 1, 1, 12, 0, 0),
            end=datetime(2023, 1, 1, 13, 0, 0),
            summary="Recurring Event",
            rrule="FREQ=DAILY;COUNT=5",
        )
    ]
    recurring_calendar = create_test_ical_calendar(recurring_events)
    recurring_path = os.path.join(base_path, "recurring.ics")
    with open(recurring_path, "w") as f:
        f.write(recurring_calendar)
    files["recurring"] = recurring_path

    # Create all_day.ics
    all_day_events = [
        generate_all_day_ical_event(
            uid="allday1@example.com",
            date=datetime(2023, 1, 1),
            summary="All Day Event 1",
        ),
        generate_all_day_ical_event(
            uid="allday2@example.com",
            date=datetime(2023, 1, 2),
            summary="All Day Event 2",
        ),
    ]
    all_day_calendar = create_test_ical_calendar(all_day_events)
    all_day_path = os.path.join(base_path, "all_day.ics")
    with open(all_day_path, "w") as f:
        f.write(all_day_calendar)
    files["all_day"] = all_day_path

    # Create timezone.ics
    timezone_events = [
        generate_timezone_ical_event(
            uid="timezone1@example.com",
            start=datetime(2023, 1, 1, 12, 0, 0),
            end=datetime(2023, 1, 1, 13, 0, 0),
            summary="Timezone Event 1",
            timezone="America/New_York",
        )
    ]
    timezone_calendar = create_test_ical_calendar(timezone_events)
    timezone_path = os.path.join(base_path, "timezone.ics")
    with open(timezone_path, "w") as f:
        f.write(timezone_calendar)
    files["timezone"] = timezone_path

    return files
