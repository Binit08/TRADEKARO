# Metrics Engine

## What it is
The `MetricsEngine` is the post-processing analytical suite. It takes the raw log of executed trades and the daily equity curve to generate institutional-grade performance statistics.

## Why it exists
Raw execution logs are unreadable for humans. The system needs to calculate standardized industry metrics like the Sharpe Ratio, Maximum Drawdown, Win Rate, and Profit Factor so traders can objectively evaluate strategy performance against benchmarks.

## Data Flow
1. Sits idle during the high-speed tick-by-tick simulation loop to conserve CPU cycles.
2. Once the loop finishes, the `BacktestEngine` passes the full `trade_log` and `equity_curve` lists to the Metrics Engine.
3. Uses `numpy` and `pandas` to calculate vectorized performance statistics.
4. Specifically calculates Max Drawdown by tracking the rolling peak of the equity curve.
5. Returns a structured `MetricsReport` dictionary which is serialized into JSON and sent back to the NLconverter frontend for charting.

## Source Code Reference

::: app.metrics.metrics_engine
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
