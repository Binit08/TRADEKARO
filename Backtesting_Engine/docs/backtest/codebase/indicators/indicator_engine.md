# Indicator Engine

## What it is
The `IndicatorEngine` is a stateful mathematical processor that wraps `TA-Lib` and `pandas-ta` to calculate technical indicators in real-time as new market data arrives.

## Why it exists
Unlike simple vectorized pandas operations which calculate an entire column at once, a backtester must simulate real-time data flow. Calculating a 200-day moving average on every single 1-minute tick by slicing arrays is catastrophically slow. The `IndicatorEngine` maintains highly optimized, fixed-size rolling windows in memory to compute indicators in $O(1)$ time.

## Data Flow
1. Before the loop starts, scans the AST to determine exactly which indicators are required (e.g., RSI 14, SMA 50).
2. As a `MarketEvent` tick arrives, it appends the new `close` price to its internal `collections.deque` rolling windows.
3. Computes the latest indicator values using TA-Lib's stream functions.
4. Caches the result in a fast dictionary.
5. The `SignalEngine` requests these cached values moments later to evaluate the trading logic.

## Source Code Reference

::: app.indicators.indicator_engine
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
