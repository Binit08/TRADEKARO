# Routes

## What it is
The `routes.py` file maps specific HTTP endpoints (like `/run_backtest`) to the internal Python functions that orchestrate the simulation.

## Why it exists
It enforces the separation of concerns. The HTTP logic (parsing headers, returning JSON responses, handling 500 errors) is kept entirely separate from the mathematical execution logic inside `core/backtest_engine.py`.

## Data Flow
1. Receives a validated `RunBacktestRequest` from Pydantic.
2. Extracts the `strategy_ast` and `execution_context`.
3. Instantiates a completely isolated `BacktestEngine` instance (Factory Pattern).
4. Executes `engine.run()` synchronously.
5. Captures the resulting metrics and trade log.
6. Returns a `BacktestResponse` JSON payload back to the client.

## Source Code Reference

::: app.api.routes
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
