# Backtest Engine

## What it is
The `BacktestEngine` is the central orchestrator of the entire execution simulation. It binds together the Data Loader, Indicator Engine, Signal Evaluator, and Execution Simulator into a single cohesive event loop.

## Why it exists
Trading platforms require perfect state isolation to run multiple concurrent backtests without data corruption. By wrapping the entire logic inside this engine object and utilizing the Factory pattern in FastAPI, the system guarantees thread-safe, immutable memory footprints for every incoming user request.

## Data Flow
1. **Setup Phase**: Receives the user's AST and downloads required data via `MarketDataLoader`.
2. **Iteration Phase**: Enters a chronological `for` loop over the `HistoricalReplayFeed`.
3. **Tick Sync**: For every `MarketEvent` tick:
    - Calculates active indicators.
    - Evaluates the strategy logic AST.
    - Simulates trades via `ExecutionEngine`.
    - Updates portfolio margins and cash.
4. **Teardown**: Compiles all executed trades and passes them to the `MetricsEngine` to generate the final JSON response.

## Source Code Reference

::: app.core.backtest_engine
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
