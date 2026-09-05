import pytest
from unittest.mock import Mock
from datetime import datetime, timezone
from app.risk.risk_engine import RiskEngine
from app.domain.events import TickEvent
from app.domain.orders import OrderIntent
from app.portfolio.portfolio import Portfolio
from app.portfolio.position import Position

def test_risk_engine_validates_margin():
    emitted = []
    def on_approved(intent):
        emitted.append(intent)
        
    portfolio = Portfolio(initial_cash=0.0) # No cash!
    portfolios = {"RELIANCE": portfolio}
    
    engine = RiskEngine("test", portfolios, on_approved)
    
    intent = OrderIntent(
        order_intent_id="i1",
        session_id="test",
        symbol="RELIANCE",
        timestamp=datetime.now(timezone.utc),
        side="BUY",
        quantity=10,
        order_type="MARKET",
        reason="STRATEGY_ENTRY"
    )
    
    engine.process_order_intent(intent)
    assert len(emitted) == 0 # Rejected due to insufficient funds

    # Give it cash
    portfolio.cash = 10000.0
    engine.process_order_intent(intent)
    assert len(emitted) == 1 # Approved
    assert emitted[0].order_intent_id == "i1"


def test_risk_engine_triggers_stop_loss():
    emitted = []
    def on_approved(intent):
        emitted.append(intent)
        
    portfolio = Portfolio(initial_cash=10000.0)
    # Mock an open long position
    portfolio.positions["RELIANCE"] = Position(
        symbol="RELIANCE",
        qty=10,
        entry_price=100.0,
        entry_time=datetime.now(timezone.utc),
        current_price=100.0,
        unrealized_pnl=0.0,
        side="LONG",
        stop_loss=90.0,
        take_profit=120.0
    )
    portfolios = {"RELIANCE": portfolio}
    
    engine = RiskEngine("test", portfolios, on_approved)
    
    # Tick below stop loss
    tick = TickEvent(
        event_id="t1",
        session_id="test",
        instrument_token=1,
        symbol="RELIANCE",
        timestamp=datetime.now(timezone.utc),
        last_price=89.0,
        volume=100
    )
    
    engine.on_tick(tick)
    
    assert len(emitted) == 1
    intent = emitted[0]
    
    assert intent.symbol == "RELIANCE"
    assert intent.side == "SELL"
    assert intent.reason == "STOP_LOSS"
    assert intent.quantity == 10
