import pytest
from datetime import datetime, timezone
from app.domain.events import TickEvent, CandleEvent, PortfolioUpdateEvent, PositionUpdateEvent, SessionStatusEvent
from app.domain.orders import OrderIntent, OrderFill
from app.domain.session import SessionStatus
from dataclasses import FrozenInstanceError

def test_tick_event():
    now = datetime.now(timezone.utc)
    event = TickEvent(
        event_id="tick-1",
        session_id="session-1",
        instrument_token=738561,
        symbol="RELIANCE",
        timestamp=now,
        last_price=100.5,
        volume=10
    )
    
    assert event.event_id == "tick-1"
    assert event.last_price == 100.5
    
    with pytest.raises(FrozenInstanceError):
        event.last_price = 101.0

def test_candle_event():
    now = datetime.now(timezone.utc)
    event = CandleEvent(
        event_id="candle-1",
        session_id="session-1",
        instrument_token=738561,
        symbol="RELIANCE",
        timeframe="1m",
        timestamp=now,
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5
    )
    
    assert event.close == 100.5
    with pytest.raises(FrozenInstanceError):
        event.close = 101.0

def test_order_intent():
    now = datetime.now(timezone.utc)
    intent = OrderIntent(
        order_intent_id="intent-1",
        session_id="session-1",
        symbol="RELIANCE",
        timestamp=now,
        side="BUY",
        quantity=10,
        order_type="MARKET",
        reason="STRATEGY_ENTRY"
    )
    
    assert intent.side == "BUY"
    assert intent.reason == "STRATEGY_ENTRY"
    with pytest.raises(FrozenInstanceError):
        intent.quantity = 20

def test_order_fill():
    now = datetime.now(timezone.utc)
    fill = OrderFill(
        fill_id="fill-1",
        session_id="session-1",
        order_intent_id="intent-1",
        symbol="RELIANCE",
        timestamp=now,
        side="BUY",
        filled_quantity=10,
        filled_price=100.5,
        fees=2.0,
        slippage=0.1
    )
    
    assert fill.filled_quantity == 10
    assert fill.fees == 2.0

def test_session_status():
    assert SessionStatus.CREATED == "CREATED"
    assert SessionStatus.RUNNING == "RUNNING"
