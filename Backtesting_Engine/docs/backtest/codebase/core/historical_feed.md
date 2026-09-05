# Historical Feed

## What it is
The `historical_feed.py` module implements the core Historical Feed functionality. It defines key architectural components including `HistoricalReplayFeed`.

**Overview**: Historical replay feed engine.

## Why it exists
To maintain strict separation of concerns within the `core` domain, this module isolates the Historical Feed logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (internal methods).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: app.core.historical_feed
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
