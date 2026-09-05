# Instruments

## What it is
The `instruments.py` module implements the core Instruments functionality.

## Why it exists
To maintain strict separation of concerns within the `api` domain, this module isolates the Instruments logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (`get_instruments`, `get_futures`).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: backend.api.routers.instruments
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
