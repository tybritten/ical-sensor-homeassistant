# Sample iCal Files for Testing

This directory contains sample iCal files used for testing the iCal Home Assistant custom component. Each file represents a different scenario to ensure comprehensive test coverage.

## Sample Files

### basic.ics
- Simple events without recurrence
- Standard start and end times
- Basic event properties (summary, description, location)

### recurring.ics
- Events with RRULE patterns
- Daily, weekly, monthly recurrence
- Events with UNTIL and COUNT parameters
- Events with EXDATE (excluded dates)

### all_day.ics
- All-day events (no time component)
- Events spanning multiple days
- Events with timezone information

### timezone.ics
- Events with various timezone information
- UTC events
- Local timezone events
- Events with different timezones

### complex.ics
- Combination of different event types
- Events with attachments and categories
- Events with complex descriptions
- Edge cases and special scenarios

## Usage in Tests

These files will be used to:
1. Test iCal parsing functionality
2. Validate recurring event processing
3. Ensure proper timezone handling
4. Verify event filtering by date range
5. Test error handling with malformed iCal data
