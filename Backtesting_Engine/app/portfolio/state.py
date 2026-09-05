"""Portfolio state model."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PortfolioState:
    """Snapshot of portfolio-level accounting metrics."""

    cash: float
    equity: float
    realized_pnl: float
    unrealized_pnl: float
    drawdown: float
    open_positions: int
    closed_positions: int
