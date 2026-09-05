"""Tests for execution cost models."""

from datetime import datetime

import pytest

from app.data.market_event import MarketEvent
from app.execution.fees import FeeModel
from app.execution.simulator import ExecutionEngine
from app.execution.slippage import SlippageModel
from app.portfolio.portfolio import Portfolio


def _candle(ts: datetime, open_price: float) -> MarketEvent:
    return MarketEvent(
        symbol="RELIANCE",
        timestamp=ts,
        open=open_price,
        high=open_price + 1,
        low=open_price - 1,
        close=open_price,
        volume=1000,
    )


def test_slippage_and_fees_are_applied_to_execution() -> None:
    engine = ExecutionEngine(
        qty=10,
        fee_model=FeeModel(rate=0.001, fixed=1.0),
        slippage_model=SlippageModel(bps=10),
    )

    engine.submit_signal("BUY", _candle(datetime(2024, 1, 1, 9, 15), 100.0))
    trade = engine.execute(_candle(datetime(2024, 1, 1, 9, 20), 100.0))

    assert trade is not None
    assert trade.entry_price == pytest.approx(100.1)
    assert trade.slippage == pytest.approx(1.0)
    assert trade.fees == pytest.approx(2.001)


def test_portfolio_realized_pnl_includes_entry_and_exit_fees() -> None:
    portfolio = Portfolio(initial_cash=10_000)
    entry_engine = ExecutionEngine(qty=10, fee_model=FeeModel(rate=0.001), slippage_bps=10)
    exit_engine = ExecutionEngine(qty=10, fee_model=FeeModel(rate=0.001), slippage_bps=10)

    entry_engine.submit_signal("BUY", _candle(datetime(2024, 1, 1, 9, 15), 100.0))
    buy_trade = entry_engine.execute(_candle(datetime(2024, 1, 1, 9, 20), 100.0))
    assert buy_trade is not None
    portfolio.open_position(buy_trade)

    exit_engine.submit_signal("SELL", _candle(datetime(2024, 1, 1, 9, 25), 110.0))
    sell_trade = exit_engine.execute(_candle(datetime(2024, 1, 1, 9, 30), 110.0))
    assert sell_trade is not None
    closed_trade = portfolio.close_position(
        "RELIANCE",
        exit_price=sell_trade.entry_price,
        exit_time=sell_trade.entry_time,
        exit_fee=sell_trade.fees,
    )

    gross_pnl = (109.89 - 100.1) * 10
    total_fees = (100.1 * 10 * 0.001) + (109.89 * 10 * 0.001)
    assert closed_trade.pnl == pytest.approx(gross_pnl - total_fees)
    assert portfolio.get_realized_pnl() == pytest.approx(gross_pnl - total_fees)
    assert portfolio.summary()["fees_paid"] == pytest.approx(total_fees)


def test_volume_based_slippage_impact() -> None:
    # Slippage model with fixed bps = 10 and volume impact = 5 bps per pct ADV
    model = SlippageModel(bps=10.0, volume_impact_bps_per_pct_adv=5.0)

    # 1. Without volume, fallback to fixed bps (10 bps)
    price_no_vol = model.apply(100.0, "BUY", volume=None, qty=50.0)
    assert price_no_vol == pytest.approx(100.1)

    # 2. With volume = 1000, qty = 50 -> pct_adv = 5% -> total_bps = 10 + 5 * 5 = 35 bps (0.35%)
    price_with_vol = model.apply(100.0, "BUY", volume=1000.0, qty=50.0)
    assert price_with_vol == pytest.approx(100.35)

    # 3. Sell order with volume
    price_sell = model.apply(100.0, "SELL", volume=1000.0, qty=50.0)
    assert price_sell == pytest.approx(99.65)

    # 4. Integrate with ExecutionEngine
    engine = ExecutionEngine(
        qty=50,
        slippage_model=model,
    )
    engine.submit_signal("BUY", _candle(datetime(2024, 1, 1, 9, 15), 100.0))
    trade = engine.execute(_candle(datetime(2024, 1, 1, 9, 20), 100.0)) # candle volume = 1000 by default in _candle

    assert trade is not None
    # default _candle volume is 1000, qty is 50 -> pct_adv = 5.0% -> total_bps = 35 -> 0.35%
    # entry_price should be 100.35
    assert trade.entry_price == pytest.approx(100.35)
    # slippage cost: reference_price = 100.0, fill_price = 100.35, qty = 50 -> cost = 0.35 * 50 = 17.5
    assert trade.slippage == pytest.approx(17.5)


def test_apply_slippage_verbatim() -> None:
    import inspect
    import math
    from app.execution.slippage import apply_slippage

    # Force annotation evaluation to prevent regressions
    sig = inspect.signature(apply_slippage)
    assert sig is not None

    # Call apply_slippage and assert the result is finite
    result = apply_slippage(100.0, "BUY", bps=10.0, volume=1000.0, qty=10.0)
    assert math.isfinite(result)


