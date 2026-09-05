# Portfolio

## What it is
The `Portfolio` acts as the master ledger and risk-management system during a simulation. It tracks active positions, available cash, realized P&L, and margin utilization.

## Why it exists
To accurately backtest leveraged instruments (Futures/Options) or complex position-sizing algorithms, the system must maintain a strict, stateful ledger of capital. The `Portfolio` object ensures that a strategy cannot over-leverage itself or trade with imaginary money.

## Data Flow
1. Initialized at the start of a backtest with `initial_capital` (e.g., $100,000).
2. As the `ExecutionSimulator` fires trades, the Portfolio creates or updates `Position` objects.
3. Deducts required margin from the `available_cash` pool.
4. On every tick, the engine calls `update_market_prices()` to recalculate the unrealized Mark-To-Market (MTM) P&L of all open positions.
5. If a position is closed, frees up the margin and adds the realized P&L back to the cash pool.

## Source Code Reference

::: app.portfolio.portfolio
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
