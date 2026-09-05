# Models

## What it is
This module defines the Pydantic data schemas used exclusively for validating incoming HTTP requests to the Backtesting Engine. It defines the exact JSON structure required to trigger a simulation.

## Why it exists
Pydantic models act as a strict type-safety gate. If the NLconverter accidentally sends a malformed AST, a string instead of a float for slippage, or an invalid date, Pydantic immediately rejects the request with a 422 Unprocessable Entity error before the engine wastes CPU cycles attempting to parse it.

## Data Flow
1. A POST request hits `/api/v1/run_backtest`.
2. FastAPI automatically passes the JSON payload into the `RunBacktestRequest` Pydantic model.
3. Pydantic validates all fields (e.g., `strategy_ast`, `start_date`, `symbols`).
4. If valid, the populated object is passed to the execution route handler.

## Source Code Reference

::: app.api.models
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
