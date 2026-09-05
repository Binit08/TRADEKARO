"""Tests for Portfolio Engine V1.

Integration flow example:
Trade -> Portfolio.open_position() -> cash update -> mark_to_market() -> pnl/equity
"""
from __future__ import annotations

from datetime import datetime

from app.data.market_event import MarketEvent
from app.execution.trade import Trade
from app.portfolio.portfolio import Portfolio


def _trade_buy(price: float = 104.0, qty: float = 100.0) -> Trade:
    return Trade(
        symbol="RELIANCE",
        side="BUY",
        entry_price=price,
        qty=qty,
        entry_time=datetime(2024, 1, 1, 9, 20),
    )


def _candle(price: float, ts: datetime | None = None) -> MarketEvent:
    ts = ts or datetime(2024, 1, 1, 9, 25)
    return MarketEvent(
        symbol="RELIANCE",
        timestamp=ts,
        open=price,
        high=price + 1,
        low=price - 1,
        close=price,
        volume=1000,
    )


def test_open_position() -> None:
    portfolio = Portfolio(initial_cash=100000)
    portfolio.open_position(_trade_buy(price=104, qty=100))

    assert portfolio.get_cash() == 89600
    assert len(portfolio.positions) == 1


def test_close_position() -> None:
    portfolio = Portfolio(initial_cash=100000)
    portfolio.open_position(_trade_buy(price=104, qty=100))

    portfolio.close_position("RELIANCE", exit_price=109, exit_time=datetime(2024, 1, 1, 10, 0))

    # realized pnl = (109 - 104) * 100 = 500
    assert portfolio.get_realized_pnl() == 500
    assert portfolio.get_cash() == 100500
    assert len(portfolio.positions) == 0


def test_mark_to_market() -> None:
    portfolio = Portfolio(initial_cash=100000)
    portfolio.open_position(_trade_buy(price=104, qty=100))

    portfolio.mark_to_market(_candle(price=109))

    # unrealized pnl = (109 - 104) * 100 = 500
    assert portfolio.get_unrealized_pnl() == 500


def test_equity() -> None:
    portfolio = Portfolio(initial_cash=100000)
    portfolio.open_position(_trade_buy(price=104, qty=100))

    portfolio.mark_to_market(_candle(price=109))

    # equity = cash + position value = 89600 + 109*100 = 100500
    assert portfolio.get_equity() == 100500


def test_drawdown() -> None:
    portfolio = Portfolio(initial_cash=100000)
    portfolio.open_position(_trade_buy(price=104, qty=100))

    # Up move (new max equity)
    portfolio.mark_to_market(_candle(price=110, ts=datetime(2024, 1, 1, 9, 30)))
    assert portfolio.get_equity() == 100600

    # Down move from peak
    portfolio.mark_to_market(_candle(price=100, ts=datetime(2024, 1, 1, 9, 35)))

    assert portfolio.get_equity() == 99600
    assert portfolio.get_drawdown() > 0


def test_summary() -> None:
    portfolio = Portfolio(initial_cash=100000)
    portfolio.open_position(_trade_buy(price=104, qty=100))
    portfolio.mark_to_market(_candle(price=106))

    summary = portfolio.summary()

    assert summary["cash"] == 89600
    assert summary["equity"] == 100200
    assert summary["realized_pnl"] == 0
    assert summary["unrealized_pnl"] == 200
    assert summary["positions"] == 1


def test_short_accounting_entry() -> None:
    # 50k short on 100k cash
    # short_margin_pct = 0.5
    # cash = 75k - fees (since margin requirement = 25k is locked up)
    # collateral = 75k (margin + short sale proceeds)
    # equity = 100k - fees (at entry, no price change)
    portfolio = Portfolio(initial_cash=100000.0, short_margin_pct=0.5)
    trade = Trade(
        symbol="RELIANCE",
        side="SELL",
        entry_price=100.0,
        qty=500.0, # 500 * 100 = 50,000 notional
        entry_time=datetime(2024, 1, 1, 9, 20),
        fees=150.0, # mock fees
        intent="ENTRY",
    )
    portfolio.open_position(trade)

    assert portfolio.get_cash() == 75000.0 - 150.0
    assert portfolio.collateral == 75000.0

    # Recalculate equity using mark_to_market
    portfolio.mark_to_market(_candle(price=100.0))
    assert portfolio.get_equity() == 100000.0 - 150.0


def test_short_mtm_at_three_prices() -> None:
    # 50k short on 100k cash
    # short_margin_pct = 0.5
    # entry_fee = 150.0, exit_fee = 100.0
    portfolio = Portfolio(initial_cash=100000.0, short_margin_pct=0.5)
    trade = Trade(
        symbol="RELIANCE",
        side="SELL",
        entry_price=100.0,
        qty=500.0,
        entry_time=datetime(2024, 1, 1, 9, 20),
        fees=150.0,
        intent="ENTRY",
    )
    portfolio.open_position(trade)

    # 1. At entry (price = 100.0)
    portfolio.mark_to_market(_candle(price=100.0))
    assert portfolio.get_cash() == 74850.0
    assert portfolio.collateral == 75000.0
    assert portfolio.get_equity() == 99850.0  # initial cash - entry_fee

    # 2. At profitable price (price = 90.0)
    # PnL = +5,000
    portfolio.mark_to_market(_candle(price=90.0))
    assert portfolio.get_cash() == 74850.0
    assert portfolio.collateral == 75000.0
    assert portfolio.get_equity() == 104850.0  # 99850 + 5000

    # 3. At losing price (price = 110.0)
    # PnL = -5,000
    portfolio.mark_to_market(_candle(price=110.0))
    assert portfolio.get_cash() == 74850.0
    assert portfolio.collateral == 75000.0
    assert portfolio.get_equity() == 94850.0  # 99850 - 5000

    # 4. At close (exit_price = 90.0, exit_fee = 100.0)
    # closed PnL = 5000 - 250 (fees) = 4750
    # equity = 100000 - 250 + 5000 = 104750
    closed_trade = portfolio.close_position(
        symbol="RELIANCE",
        exit_price=90.0,
        exit_time=datetime(2024, 1, 1, 9, 40),
        exit_fee=100.0,
    )
    assert closed_trade.pnl == 4750.0
    assert portfolio.get_cash() == 104750.0
    assert portfolio.collateral == 0.0

    # Mark to market at exit candle to trigger MTM/equity recalculation for the bar
    portfolio.mark_to_market(_candle(price=90.0, ts=datetime(2024, 1, 1, 9, 40)))
    assert portfolio.get_equity() == 104750.0


def test_close_position_fee_accounting() -> None:
    portfolio = Portfolio(initial_cash=100000.0)
    
    trade_entry = Trade(
        symbol="RELIANCE",
        side="BUY",
        entry_price=100.0,
        qty=100.0,
        entry_time=datetime(2024, 1, 1, 9, 20),
        fees=10.0,
        intent="ENTRY",
    )
    portfolio.open_position(trade_entry)
    assert portfolio.fees_paid == 10.0

    trade_exit = portfolio.close_position(
        symbol="RELIANCE",
        exit_price=110.0,
        exit_time=datetime(2024, 1, 1, 9, 30),
        exit_fee=15.0,
    )
    
    assert trade_exit.fees == 25.0
    assert trade_exit.entry_fee == 10.0
    assert trade_exit.exit_fee == 15.0
    assert portfolio.fees_paid == 25.0
    
    gross = (110.0 - 100.0) * 100.0
    assert trade_exit.pnl == gross - 25.0





