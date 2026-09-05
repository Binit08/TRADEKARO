# Main

## What it is
This is the primary application entry point for the Backtesting Engine. It exposes a Command Line Interface (CLI) for executing standalone historical data downloads and backtest simulations without needing to boot the FastAPI server.

## Why it exists
While the engine is typically accessed via the API (Port 8002), quantitative researchers often need to run massive, multi-year backtests locally. The CLI bypasses the network overhead and HTTP timeouts, allowing for direct, long-running execution of strategy JSON files.

## Data Flow
1. Parses CLI arguments (`--strategy`, `--start`, `--end`, `--symbols`).
2. If `--download` is passed, it triggers the `fetch_historical` loader to cache data as `.parquet`.
3. Reads the `.json` strategy file into memory.
4. Instantiates the `BacktestEngine` and runs the core loop synchronously.
5. Outputs the final `MetricsReport` directly to `stdout`.

## Source Code Reference

::: app.main
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
