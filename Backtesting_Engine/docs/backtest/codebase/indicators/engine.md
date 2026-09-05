# Engine

## What it is
The `engine.py` module implements the core Engine functionality. It defines key architectural components including `IndicatorEngine`.

**Overview**: Indicator Pre-computation Engine.

## Why it exists
To maintain strict separation of concerns within the `indicators` domain, this module isolates the Engine logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (internal methods).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: app.indicators.engine
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
