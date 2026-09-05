# Simulator

## What it is
The `ExecutionSimulator` is a highly deterministic trade matching engine. It receives buy/sell signals from the AST Evaluator and simulates exactly how those trades would be executed in a live brokerage environment.

## Why it exists
Without slippage, commission, and latency simulation, backtest results are notoriously overly optimistic. The simulator introduces real-world friction to ensure the backtest metrics perfectly mirror live trading constraints.

## Data Flow
1. Receives a `SignalEvent` (e.g. `BUY AAPL`) from the `SignalEngine`.
2. Intercepts the current market price from the `HistoricalReplayFeed`.
3. Calculates realistic fill prices by applying Slippage basis points (bps). For a BUY, the price is shifted upward; for a SELL, downward.
4. Requests the `Portfolio` module to reserve margin and check if the user has sufficient cash to open the position.
5. If cash is sufficient, logs an executed `TradeEvent` and deducts the commission fee.
6. If cash is insufficient, rejects the trade to prevent negative simulated balances.

## Source Code Reference

::: app.execution.simulator
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
