# Backtests

## What it is
The `backtests.py` router is the API entrypoint for executing and retrieving historical simulations from the frontend UI.

## Why it exists
By placing this router in the NLconverter rather than exposing the core engine directly, the system enforces secure authentication (via Supabase JWTs), rate limiting, and database persistence. It acts as a necessary security proxy before mathematical execution occurs on port 8002.

## Data Flow
1. **POST /backtest**: Accepts a `ProxyBacktestRequest` containing the user's generated JSON AST.
2. **Validation**: Maps requested symbols to exchange formats (e.g. `NIFTY` -> `NSE:NIFTY50`).
3. **Proxy Execution**: Calls `run_backtest_api()` which makes a blocking HTTP POST to the internal engine on port 8002.
4. **Data Normalization**: Transforms the massive, engine-specific response into a standardized frontend format (normalizing `LONG`/`SHORT` nomenclature and timestamp formatting).
5. **Persistence**: Saves the exact AST, all slippage/margin inputs, and the resulting equity curves into the `BacktestRecord` PostgreSQL/SQLite table for reproducible auditing.
6. **Response**: Returns the chart-ready JSON to the Next.js client.

## Source Code Reference

::: backend.api.routers.backtests
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
