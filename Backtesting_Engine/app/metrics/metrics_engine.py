"""Metrics Engine V1 for historical backtesting performance stats.

Computes core performance statistics from portfolio outputs:
- equity_history
- trade_history

Constraints:
- Historical backtest only
- No Sharpe/Sortino/CAGR/benchmark metrics in V1
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List
import math

from app.metrics.models import MetricsSnapshot


class MetricsEngine:
    """Compute and store latest backtest performance metrics."""

    def __init__(self) -> None:
        self._latest: Dict[str, Any] = {}

    def reset(self) -> None:
        """Reset the metrics engine between backtest runs."""
        self._latest.clear()

    @staticmethod
    def _extract_trade_pnl(trade: Any) -> float:
        """Extract PnL from a trade object or dict.

        Supported formats:
        - dict with `pnl`
        - dataclass/object with `pnl`
        """
        if isinstance(trade, dict):
            status = trade.get("status")
            if status is not None and str(status).upper() == "OPEN":
                return 0.0
            if "pnl" in trade and trade["pnl"] is not None:
                return float(trade["pnl"])
            raise ValueError("Trade dictionary must carry 'pnl'")

        # object/dataclass branch
        status = getattr(trade, "status", None)
        if status is not None and str(status).upper() == "OPEN":
            return 0.0
        if hasattr(trade, "pnl") and getattr(trade, "pnl") is not None:
            return float(getattr(trade, "pnl"))
        raise ValueError("Trade object must carry 'pnl'")

    @staticmethod
    def _max_drawdown_pct(equity_history: List[float]) -> float:
        """Compute max drawdown percentage from equity curve."""
        if not equity_history:
            return 0.0

        peak = float(equity_history[0])
        max_dd = 0.0
        for eq in equity_history:
            eqf = float(eq)
            if eqf > peak:
                peak = eqf
            if peak > 0:
                dd = ((peak - eqf) / peak) * 100.0
                if dd > max_dd:
                    max_dd = dd
        return max_dd

    @staticmethod
    def _streaks(pnls: Iterable[float]) -> tuple[int, int]:
        """Return (longest_win_streak, longest_loss_streak).

        Streak Convention:
        - Winning trades (PnL > 0) increment the win streak and reset the loss streak.
        - Losing trades (PnL < 0) increment the loss streak and reset the win streak.
        - Break-even trades (PnL == 0) reset both winning and losing streaks back to zero
          (i.e. break-even trades do not continue any streak).
        """
        longest_win = 0
        longest_loss = 0
        cur_win = 0
        cur_loss = 0

        for pnl in pnls:
            if pnl > 0:
                cur_win += 1
                cur_loss = 0
            elif pnl < 0:
                cur_loss += 1
                cur_win = 0
            else:
                cur_win = 0
                cur_loss = 0

            if cur_win > longest_win:
                longest_win = cur_win
            if cur_loss > longest_loss:
                longest_loss = cur_loss

        return longest_win, longest_loss

    def compute(
        self,
        equity_history: List[float],
        trade_history: List[Any],
        portfolio_unrealized_pnl: float = 0.0,
        equity_curve: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compute V1 performance metrics.

        Returns a flat dict for downstream reporting.

        Accounting Drift:
        - `accounting_drift` measures the difference between change in total portfolio equity
          (final_equity - initial_equity) and the sum of realized and unrealized trade PnLs.
          In a consistent accounting system, this difference should be within floating-point tolerance.

        Note:
        - Summing `fees` across `trade_history` (or `portfolio.trade_history`) already
          includes both sides of a round trip (both entry and exit fees).
        """
        # Equity-level metrics
        if equity_history:
            initial = float(equity_history[0])
            if initial <= 0:
                raise ValueError("Initial equity must be greater than zero")
            final = float(equity_history[-1])
            return_pct = ((final - initial) / initial) * 100.0 if initial != 0 else 0.0
            net_pnl = final - initial
        else:
            return_pct = 0.0
            net_pnl = 0.0

        if equity_curve:
            drawdowns = [float(r.get("drawdown_pct", 0.0)) for r in equity_curve]
            max_drawdown = max(drawdowns) if drawdowns else 0.0
            
            # Compute Sharpe and Sortino
            sharpe_ratio = None
            sortino_ratio = None
            if len(equity_curve) > 1:
                daily_returns = []
                prev_eq = float(equity_curve[0]["equity"])
                for r in equity_curve[1:]:
                    curr_eq = float(r["equity"])
                    if prev_eq > 0:
                        daily_returns.append((curr_eq - prev_eq) / prev_eq)
                    prev_eq = curr_eq
                
                if daily_returns:
                    mean_ret = sum(daily_returns) / len(daily_returns)
                    variance = sum((r - mean_ret) ** 2 for r in daily_returns) / len(daily_returns)
                    std_dev = math.sqrt(variance) if variance > 0 else 0.0
                    
                    downside_returns = [r for r in daily_returns if r < 0]
                    downside_variance = sum(r ** 2 for r in downside_returns) / len(daily_returns) if daily_returns else 0.0
                    downside_dev = math.sqrt(downside_variance) if downside_variance > 0 else 0.0
                    
                    annualized_return = mean_ret * 252
                    annualized_vol = std_dev * math.sqrt(252)
                    annualized_downside_vol = downside_dev * math.sqrt(252)
                    
                    risk_free_rate = 0.0
                    if annualized_vol > 0:
                        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_vol
                    if annualized_downside_vol > 0:
                        sortino_ratio = (annualized_return - risk_free_rate) / annualized_downside_vol
        else:
            max_drawdown = self._max_drawdown_pct(equity_history)
            sharpe_ratio = None
            sortino_ratio = None

        # Trade-level metrics
        total_trades = len(trade_history)
        
        def is_open(t: Any) -> bool:
            status = t.get("status") if isinstance(t, dict) else getattr(t, "status", None)
            return status is not None and str(status).upper() == "OPEN"
            
        trade_pnls = [
            self._extract_trade_pnl(t)
            for t in trade_history
            if not is_open(t)
        ]
        
        closed_trades = len(trade_pnls)
        open_trades = total_trades - closed_trades

        wins = [p for p in trade_pnls if p > 0]
        losses = [p for p in trade_pnls if p < 0]
        break_evens = [p for p in trade_pnls if p == 0]

        winning_trades = len(wins)
        losing_trades = len(losses)
        break_even_trades = len(break_evens)
        resolved_trades = winning_trades + losing_trades
        
        realized_pnl = sum(trade_pnls)
        unrealized_pnl = portfolio_unrealized_pnl
        accounting_drift = net_pnl - (realized_pnl + unrealized_pnl)

        warnings = []
        tolerance = 1e-6 * abs(net_pnl) if abs(net_pnl) > 0 else 1e-6
        if abs(accounting_drift) > tolerance:
            warnings.append(
                f"Significant accounting drift detected: {accounting_drift:.6f} "
                f"(tolerance threshold: {tolerance:.6f})"
            )

        if closed_trades > 0:
            if resolved_trades > 0:
                win_rate = (winning_trades / resolved_trades) * 100.0
            else:
                win_rate = 0.0

            average_win = sum(wins) / winning_trades if winning_trades > 0 else 0.0
            average_loss = sum(losses) / losing_trades if losing_trades > 0 else 0.0

            gross_profit = sum(wins)
            gross_loss_abs = abs(sum(losses))
            if gross_loss_abs == 0:
                profit_factor = None if gross_profit > 0 else 0.0
            else:
                profit_factor = gross_profit / gross_loss_abs
        else:
            win_rate = None
            profit_factor = None
            average_win = 0.0
            average_loss = 0.0

        largest_win = max(wins) if wins else 0.0
        largest_loss = min(losses) if losses else 0.0

        longest_win_streak, longest_loss_streak = self._streaks(trade_pnls)

        snapshot = MetricsSnapshot(
            return_pct=return_pct,
            win_rate=win_rate,
            average_win=average_win,
            average_loss=average_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            total_trades=total_trades,
            open_trades=open_trades,
            closed_trades=closed_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            break_even_trades=break_even_trades,
            net_pnl=net_pnl,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            accounting_drift=accounting_drift,
            largest_win=largest_win,
            largest_loss=largest_loss,
            longest_win_streak=longest_win_streak,
            longest_loss_streak=longest_loss_streak,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            warnings=warnings,
        )

        self._latest = snapshot.to_dict()
        return dict(self._latest)

    def summary(self) -> Dict[str, Any]:
        """Return latest computed metrics dict."""
        return dict(self._latest)
