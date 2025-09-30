# Unit Testing Plan for iCal Home Assistant Custom Component

## Overview
This document outlines the approach for adding unit tests to the iCal Home Assistant custom component. The component processes iCal calendars to create sensors for upcoming events and calendar entries.

## Component Structure Analysis
The iCal component consists of several key modules:

1. **`__init__.py`** - Main integration file containing the `ICalEvents` class which handles:
   - Fetching and parsing iCal data from URLs or local files
   - Processing recurring events (RRULE)
   - Converting dates and timezones
   - Providing events for sensors and calendar entities

2. **`calendar.py`** - Calendar platform implementation:
   - `ICalCalendarEventDevice` class for calendar entities
   - Provides upcoming events to the Home Assistant calendar

3. **`sensor.py`** - Sensor platform implementation:
   - `ICalSensor` class for individual event sensors
   - Creates multiple sensors for upcoming events

4. **`config_flow.py`** - Configuration flow for setting up the integration

5. **`const.py`** - Constants used throughout the component

## Test Directory Structure
```
tests/
├── __init__.py
├── conftest.py                 # pytest configuration and fixtures
├── test_config_flow.py         # Tests for config flow
├── test_init.py                # Tests for the main integration
├── test_calendar.py            # Tests for calendar platform
├── test_sensor.py              # Tests for sensor platform
└── fixtures/
    ├── __init__.py
    ├── sample_calendars/       # Sample iCal files for testing
    │   ├── basic.ics           # Basic calendar with simple events
    │   ├── recurring.ics       # Calendar with recurring events
    │   ├── all_day.ics         # Calendar with all-day events
    │   ├── timezone.ics        # Calendar with timezone information
    │   └── complex.ics         # Complex calendar with various event types
    └── test_utils.py           # Utility functions for tests
```

## Test Approach

### 1. Main ICalEvents Class Tests (`test_init.py`)
- Test iCal parsing functionality with various iCal formats
- Test recurring event processing (RRULE handling)
- Test date/time conversion and timezone handling
- Test event filtering by date range
- Test async_get_events method
- Test update method with mocked HTTP responses

### 2. Calendar Platform Tests (`test_calendar.py`)
- Test calendar entity creation
- Test async_get_events method
- Test async_update method
- Test event attribute extraction

### 3. Sensor Platform Tests (`test_sensor.py`)
- Test sensor entity creation
- Test sensor state updates
- Test sensor attributes
- Test multiple event sensors

### 4. Config Flow Tests (`test_config_flow.py`)
- Test configuration validation
- Test successful setup flow
- Test error handling

## Sample iCal Files for Testing
We'll create several sample iCal files to test different scenarios:

1. **basic.ics** - Simple events without recurrence
2. **recurring.ics** - Events with RRULE patterns
3. **all_day.ics** - All-day events
4. **timezone.ics** - Events with various timezone information
5. **complex.ics** - Combination of different event types

## Test Utilities and Fixtures
- Mock Home Assistant objects (hass, config_entry, etc.)
- Mock HTTP responses for URL-based calendars
- Utility functions for creating test events
- Fixtures for common test scenarios

## Dependencies and Configuration
- pytest for test framework
- pytest-asyncio for async testing
- pytest-cov for coverage reporting
- homeassistant as a test dependency

To install test dependencies:
```bash
pip install -r requirements_test.txt
```

Example requirements_test.txt:
```
pytest>=6.0
pytest-asyncio
pytest-cov
homeassistant
```

## Implementation Plan
1. Create test directory structure
2. Create sample iCal files for testing different scenarios
3. Implement unit tests for each component
4. Add test utilities and fixtures
5. Configure test runner and dependencies
6. Document how to run tests

## Running Tests
Tests will be run using pytest:
```bash
pytest tests/
```

## Code Coverage Goals
- Aim for >80% code coverage
- Focus on critical paths in iCal parsing
- Ensure all error handling paths are tested
- Test both positive and negative scenarios

## Continuous Integration
Tests should be integrated with GitHub Actions for automated testing on pull requests and pushes.
