# Testing Architecture for iCal Home Assistant Component

## Overview
This document provides a visual representation of the testing architecture for the iCal Home Assistant custom component.

## Test Architecture Diagram

```mermaid
graph TD
    A[Home Assistant iCal Component] --> B[Main Integration<br/>__init__.py]
    A --> C[Calendar Platform<br/>calendar.py]
    A --> D[Sensor Platform<br/>sensor.py]
    A --> E[Config Flow<br/>config_flow.py]
    A --> F[Constants<br/>const.py]
    
    G[Test Suite] --> H[Unit Tests]
    G --> I[Fixtures & Utilities]
    G --> J[Configuration]
    
    H --> K[test_init.py<br/>ICalEvents Tests]
    H --> L[test_calendar.py<br/>Calendar Tests]
    H --> M[test_sensor.py<br/>Sensor Tests]
    H --> N[test_config_flow.py<br/>Config Flow Tests]
    
    I --> O[test_utils.py<br/>Test Utilities]
    I --> P[Sample iCal Files<br/>fixtures/sample_calendars/]
    I --> Q[conftest.py<br/>pytest Fixtures]
    
    J --> R[pytest configuration]
    J --> S[Requirements]
    
    B --> K
    C --> L
    D --> M
    E --> N
    
    P --> K
    P --> L
    P --> M
```

## Test Data Flow

```mermaid
graph LR
    A[Sample iCal Files] --> B[ICalEvents Parser]
    B --> C[Calendar Entity]
    B --> D[Sensor Entities]
    E[Mock HTTP Responses] --> F[ICalEvents Update]
    F --> C
    F --> D
```

## Test Isolation Strategy

```mermaid
graph TD
    A[Unit Tests] --> B[Mock Home Assistant Core]
    A --> C[Mock External Dependencies]
    A --> D[Mock File System Access]
    A --> E[Mock Network Requests]
    
    B --> F[hass fixture]
    B --> G[config_entry fixture]
    
    C --> H[aiohttp session mock]
    C --> I[HTTP response mocks]
    
    D --> J[file:// URL handling]
    D --> K[temporary file fixtures]
    
    E --> L[webcal:// URL handling]
    E --> M[https:// URL handling]
```

## Coverage Goals

```mermaid
pie
    title Test Coverage Targets
    "Core Functionality" : 85
    "Error Handling" : 80
    "Edge Cases" : 70
    "Config Flow" : 90
```

## Integration Points

The tests will validate the following integration points:

1. **iCal Parsing Integration**
   - Direct parsing of iCal content
   - Recurring event expansion
   - Timezone conversion

2. **Home Assistant Integration**
   - Entity creation and registration
   - State updates
   - Attribute population

3. **Network Integration**
   - HTTP request handling
   - File system access
   - Error condition handling

4. **Configuration Integration**
   - User input validation
   - Config entry creation
   - Setup flow completion

## Test Execution Flow

```mermaid
graph TD
    A[pytest] --> B[conftest.py<br/>Fixture Setup]
    B --> C[test_init.py<br/>Run ICalEvents Tests]
    B --> D[test_calendar.py<br/>Run Calendar Tests]
    B --> E[test_sensor.py<br/>Run Sensor Tests]
    B --> F[test_config_flow.py<br/>Run Config Flow Tests]
    
    C --> G[Load Sample iCal Files]
    C --> H[Mock HTTP Responses]
    D --> H
    E --> H
    
    F --> I[Mock User Input]
    F --> J[Mock Validation]
```

This architecture ensures comprehensive testing of all component functionality while maintaining isolation for reliable, repeatable tests.
