"""Tests for MetricsEngine V1."""
from __future__ import annotations

import pytest

from app.metrics.metrics_engine import MetricsEngine


def _sample_equity() -> list[float]:
    return [100000, 101000, 99000, 102000]


def _sample_trades() -> list[dict]:
    # PnLs: +500, -200, +300, -100, -50, +400
    return [
        {"entry": 100, "exit": 105, "qty": 100, "pnl": 500.0},  # +500
        {"entry": 120, "exit": 118, "qty": 100, "pnl": -200.0},  # -200
        {"entry": 200, "exit": 203, "qty": 100, "pnl": 300.0},  # +300
        {"entry": 100, "exit": 99, "qty": 100, "pnl": -100.0},   # -100
        {"entry": 100, "exit": 99.5, "qty": 100, "pnl": -50.0}, # -50
        {"entry": 50, "exit": 54, "qty": 100, "pnl": 400.0},    # +400
    ]


def test_return() -> None:
    m = MetricsEngine()
    out = m.compute(_sample_equity(), _sample_trades())
    # (102000 - 100000) / 100000 * 100 = 2%
    assert out["return_pct"] == pytest.approx(2.0)


def test_win_rate() -> None:
    m = MetricsEngine()
    out = m.compute(_sample_equity(), _sample_trades())
    # 3 wins out of 6 trades = 50%
    assert out["win_rate"] == pytest.approx(50.0)
    assert out["winning_trades"] == 3
    assert out["losing_trades"] == 3
    assert out["total_trades"] == 6


def test_profit_factor() -> None:
    m = MetricsEngine()
    out = m.compute(_sample_equity(), _sample_trades())
    # gross profit = 500+300+400 = 1200
    # gross loss = 200+100+50 = 350
    assert out["profit_factor"] == pytest.approx(1200 / 350)
    assert out["average_win"] == pytest.approx(400.0)
    assert out["average_loss"] == pytest.approx(-350 / 3)


def test_drawdown() -> None:
    m = MetricsEngine()
    out = m.compute(_sample_equity(), _sample_trades())
    # Peak=101000 then trough=99000 => 1.980198%
    assert out["max_drawdown"] == pytest.approx(((101000 - 99000) / 101000) * 100)


def test_net_pnl() -> None:
    m = MetricsEngine()
    out = m.compute(_sample_equity(), _sample_trades())
    assert out["net_pnl"] == pytest.approx(2000.0)
    assert out["largest_win"] == pytest.approx(500.0)
    assert out["largest_loss"] == pytest.approx(-200.0)


def test_streaks() -> None:
    m = MetricsEngine()
    trades = [
        {"pnl": 100},
        {"pnl": 200},
        {"pnl": -50},
        {"pnl": -40},
        {"pnl": -10},
        {"pnl": 60},
    ]
    out = m.compute([100000, 100260], trades)

    assert out["longest_win_streak"] == 2
    assert out["longest_loss_streak"] == 3


def test_summary() -> None:
    m = MetricsEngine()
    computed = m.compute(_sample_equity(), _sample_trades())
    summary = m.summary()

    assert summary == computed
    assert summary["return_pct"] == pytest.approx(2.0)


def test_pnl_missing_raises() -> None:
    m = MetricsEngine()
    
    # 1. Closed trade in dictionary form missing 'pnl' raises ValueError
    with pytest.raises(ValueError, match="Trade dictionary must carry 'pnl'"):
        m._extract_trade_pnl({"status": "CLOSED", "entry": 100, "exit": 105})
        
    # 2. Closed trade in object form missing 'pnl' raises ValueError
    class DummyTradeClosed:
        status = "CLOSED"
        entry = 100
        exit = 105
        
    with pytest.raises(ValueError, match="Trade object must carry 'pnl'"):
        m._extract_trade_pnl(DummyTradeClosed())

    # 3. Open trade in dictionary form missing 'pnl' should NOT raise, returns 0.0
    assert m._extract_trade_pnl({"status": "OPEN", "entry": 100}) == 0.0

    # 4. Open trade in object form missing 'pnl' should NOT raise, returns 0.0
    class DummyTradeOpen:
        status = "OPEN"
        entry = 100
        
    assert m._extract_trade_pnl(DummyTradeOpen()) == 0.0


def test_streaks_reset_on_breakeven() -> None:
    m = MetricsEngine()
    
    # Streaks with break-even (pnl == 0) resetting both streaks
    trades = [
        {"pnl": 100.0},
        {"pnl": 0.0}, # Resets win streak
        {"pnl": 200.0},
        {"pnl": -50.0},
        {"pnl": 0.0}, # Resets loss streak
        {"pnl": -100.0},
    ]
    out = m.compute([100000.0, 100150.0], trades)
    
    assert out["longest_win_streak"] == 1
    assert out["longest_loss_streak"] == 1
    assert out["break_even_trades"] == 2


def test_accounting_drift_warnings() -> None:
    m = MetricsEngine()

    # Case 1: Drift exceeds tolerance for net_pnl > 0
    # net_pnl = 100.0. realized_pnl = 90.0, unrealized_pnl = 0.0. drift = 10.0
    # tolerance = 1e-6 * 100.0 = 1e-4. 10.0 > 1e-4 -> Warning expected
    out_drift = m.compute([100.0, 200.0], [{"pnl": 90.0}])
    assert len(out_drift["warnings"]) == 1
    assert "Significant accounting drift detected" in out_drift["warnings"][0]

    # Case 2: Drift does NOT exceed tolerance
    # net_pnl = 100.0. realized_pnl = 100.0. drift = 0.0 -> No warnings
    out_clean = m.compute([100.0, 200.0], [{"pnl": 100.0}])
    assert len(out_clean["warnings"]) == 0

    # Case 3: net_pnl == 0.0, drift exceeds absolute 1e-6 tolerance
    # net_pnl = 0.0, realized_pnl = 1.0. drift = -1.0. tolerance = 1e-6 -> Warning expected
    out_zero_pnl_drift = m.compute([100.0, 100.0], [{"pnl": 1.0}])
    assert len(out_zero_pnl_drift["warnings"]) == 1
    assert "Significant accounting drift detected" in out_zero_pnl_drift["warnings"][0]

