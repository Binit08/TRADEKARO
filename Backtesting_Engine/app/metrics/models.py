"""Models for metrics engine outputs."""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional, List

@dataclass
class MetricsSnapshot:
    """Typed snapshot of backtest performance metrics."""

    return_pct: float
    win_rate: Optional[float]
    average_win: float
    average_loss: float
    profit_factor: Optional[float]
    max_drawdown: float
    total_trades: int
    open_trades: int
    closed_trades: int
    winning_trades: int
    losing_trades: int
    break_even_trades: int
    net_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    accounting_drift: float
    largest_win: float
    largest_loss: float
    longest_win_streak: int
    longest_loss_streak: int
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return dict representation for API/report usage."""
        return asdict(self)
