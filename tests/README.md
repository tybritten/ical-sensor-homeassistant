# iCal Home Assistant Component Tests

This directory contains unit tests for the iCal Home Assistant custom component.

## Test Structure

- `test_init.py` - Tests for the main ICalEvents class
- `test_calendar.py` - Tests for the calendar platform
- `test_sensor.py` - Tests for the sensor platform
- `test_config_flow.py` - Tests for the configuration flow
- `conftest.py` - pytest configuration and fixtures
- `fixtures/` - Test utilities and sample data
  - `sample_calendars/` - Sample iCal files for testing
  - `test_utils.py` - Utility functions for tests

## Running Tests

To run the tests, first install the test dependencies:

```bash
pip install -r requirements_test.txt
```

Then run the tests using pytest:

```bash
pytest
```

For verbose output with coverage:

```bash
pytest --verbose --cov=custom_components.ical
```

## Test Coverage

The tests cover:

1. **Core Functionality** - iCal parsing, event processing, date handling
2. **Calendar Platform** - Calendar entity creation and event retrieval
3. **Sensor Platform** - Sensor entity creation and state updates
4. **Config Flow** - Configuration validation and setup flow
5. **Error Handling** - Proper handling of various error conditions
6. **Edge Cases** - All-day events, recurring events, timezone handling

## Sample iCal Files

The `fixtures/sample_calendars/` directory contains sample iCal files for testing:

- `basic.ics` - Simple events without recurrence
- `recurring.ics` - Events with RRULE patterns
- `all_day.ics` - All-day events
- `timezone.ics` - Events with timezone information
- `complex.ics` - Combination of different event types

## Continuous Integration

Tests are automatically run on GitHub Actions for all pushes and pull requests to the main branch.
