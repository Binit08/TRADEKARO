# Core Backtesting Engine

## Introduction

The Core Backtesting Engine is the computational workhorse of the ecosystem. Living entirely independent of the NLconverter, it is a high-performance, stateless FastAPI application designed exclusively to execute simulated trades against historical market data.

While the NLconverter handles the "human" aspect of trading (text, prompts, UI), the Backtesting Engine is a strict mathematical sandbox. It accepts a JSON Abstract Syntax Tree (AST), downloads historical data, iterates tick-by-tick without look-ahead bias, and outputs precise performance metrics.

---

## Internal Architecture

The Backtesting Engine relies on an **Event-Driven Architecture** mirroring institutional live-trading systems. The engine is fractured into highly specialized sub-components that communicate synchronously during the event loop.

### 1. The Market Data Loader
Located in `app/data/loader.py`, this module is responsible for the ingestion of OHLCV (Open, High, Low, Close, Volume) data.
- **Provider Agnostic**: Primarily integrates with the Zerodha Kite API, but falls back to Yahoo Finance or local `.parquet` files.
- **Caching**: Fetching years of 1-minute data over HTTP is extremely slow. The loader utilizes a dual-layer cache. First, a local disk cache (Parquet columnar storage for instant Pandas loading), and an in-memory RAM `TTLCache` to ensure that rapid iterations of a strategy do not trigger redundant network I/O.
- **Event Translation**: Crucially, the loader converts the raw Pandas DataFrame into a chronologically sorted list of `MarketEvent` dataclasses to guarantee chronological processing.

### 2. The Historical Replay Feed
Iterating over Pandas DataFrames using `.iterrows()` is slow and risks "Look-Ahead Bias" (accidentally accessing row $i+1$ during calculation $i$). 
The `HistoricalReplayFeed` yields single immutable `MarketEvent` objects one at a time. The underlying engines only ever "see" the current market snapshot, exactly as they would in a live environment.

### 3. The Indicator Engine
A stateful machine utilizing the C-based `TA-Lib` wrapper and `pandas-ta` for lightning-fast vectorized calculations. 
As each new `MarketEvent` arrives, the Indicator Engine updates its rolling windows and calculates exactly what the value of an indicator (e.g., RSI, MACD, Bollinger Bands) was at that specific timestamp.

### 4. The Signal Engine (AST Evaluator)
This is the brain of the logic simulation. It takes the JSON AST provided by the NLconverter and recursively evaluates it against the current market conditions.
- If the AST says: `IF (RSI < 30) AND (CROSS_ABOVE(SMA_50, SMA_200))`, the Signal Engine pulls those exact values from the Indicator Engine.
- If the conditions evaluate to `True`, the Signal Engine emits a strict `SignalEvent` (e.g., `BUY` or `SELL`).

### 5. The Execution Simulator & Portfolio
Once a `SignalEvent` is fired, it passes to the Execution Engine.
- **Slippage & Commission**: The Execution Engine simulates real-world friction. If slippage is set to 5 basis points, the fill price is deliberately worsened by 0.05% to simulate market impact.
- **Margin Management**: The `Portfolio` object dynamically tracks cash balances, margin requirements (for futures/options), and equity. If a simulated trade causes the available cash to drop below zero, the portfolio mathematically enforces a liquidation or rejects the signal.

### 6. The Metrics Engine
After the historical loop concludes, the Metrics Engine processes the raw execution log to generate institutional-grade performance statistics. It calculates Total Return, Max Drawdown, Sharpe Ratio, Win Rate, and Monthly Returns.

---

## State Isolation & Thread Safety

The Backtesting Engine is exposed via a FastAPI endpoint (`/api/v1/run_backtest`). Because Python runs in a multi-threaded web server environment (Uvicorn), maintaining state isolation is a matter of critical architectural importance.

**The Factory Pattern Guarantee:**
Internal components like the `Portfolio` (tracking cash) and the `IndicatorEngine` (tracking rolling windows) are inherently stateful. 
To prevent **Cross-Tenant Contamination**, the FastAPI router instantiates a completely fresh, isolated instance of the entire `BacktestEngine` class—and all its sub-components—for *every single HTTP request*. 

If User A and User B run backtests simultaneously, their `Portfolio` objects exist in entirely different memory locations, guaranteeing thread-safe mathematical purity.

---

## Configuration: The Execution Context

The logic of *when* to trade (the AST) is physically separated from the rules of *how* to trade (the Execution Context).

The Execution Context is a JSON schema submitted alongside the AST, defining:
- `position_size_type` (e.g., `PERCENT_EQUITY`, `QUANTITY`)
- `position_size`
- `commission_rate`
- `slippage_bps`
- `market_type` (e.g., `SPOT`, `FUTURES`)
- `margin` leverage ratio

This separation allows quantitative researchers to test the exact same alpha-generation logic across vastly different brokerage constraints without altering the underlying strategy code.
