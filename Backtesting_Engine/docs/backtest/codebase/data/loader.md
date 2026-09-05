# Loader

## What it is
The `MarketDataLoader` is responsible for ingesting and standardizing historical price data (OHLCV) from external brokers (like Zerodha Kite) or local Parquet storage into a chronologically guaranteed event stream.

## Why it exists
Downloading gigabytes of tick data over the internet for every backtest iteration is computationally prohibitive. The loader solves this by implementing a dual-layer caching system (local disk `.parquet` and in-memory thread-safe `TTLCache`). It also guarantees **Look-Ahead Bias prevention** by flattening raw Pandas DataFrames into a chronological stream of immutable `MarketEvent` dataclasses.

## Data Flow
1. Receives a list of symbols and date ranges.
2. Checks the RAM `TTLCache` ($O(1)$ latency).
3. If missing, calls the Kite Connect API to download the OHLCV payload.
4. Normalizes timestamps to UTC and standardizes column names.
5. Iterates through the DataFrame, converting every single row into a `MarketEvent`.
6. Merges and sorts multiple symbol streams chronologically to simulate a perfectly synced live market environment.

## Source Code Reference

::: app.data.loader
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
