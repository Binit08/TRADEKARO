# Stoploss

## What it is
The `stoploss.py` module implements the core Stoploss functionality. It defines key architectural components including `ProtectiveExit`.

**Overview**: Protective stop-loss and take-profit logic.

## Why it exists
To maintain strict separation of concerns within the `risk` domain, this module isolates the Stoploss logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (`evaluate_protective_exit`).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: app.risk.stoploss
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
