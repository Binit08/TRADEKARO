# Models

## What it is
The `models.py` module implements the core Models functionality. It defines key architectural components including `User`, `StrategyRecord`, `BacktestRecord`.

## Why it exists
To maintain strict separation of concerns within the `db` domain, this module isolates the Models logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (internal methods).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: backend.db.models
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
