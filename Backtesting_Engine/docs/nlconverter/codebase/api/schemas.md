# Schemas

## What it is
The `schemas.py` module implements the core Schemas functionality. It defines key architectural components including `Resolution`, `Universe`, `CapitalPerTrade`, `MarketType`, `StrategyRequest`, `ProxyBacktestRequest`.

## Why it exists
To maintain strict separation of concerns within the `api` domain, this module isolates the Schemas logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (internal methods).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: backend.api.schemas
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
