import pytest
from datetime import datetime, timezone
from app.strategy.engine import StrategyEngine
from app.domain.events import CandleEvent
from app.domain.orders import OrderIntent
from app.config.settings import StrategySettings

def test_strategy_engine_evaluates_and_emits():
    emitted_intents = []
    
    def on_intent(intent: OrderIntent):
        emitted_intents.append(intent)
        
    ast = {
        "schema_version": "1.0.0",
        "execution_context": {},
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "strategy_id": "test_caching",
            "operation_nodes": [
                {
                    "node_type": "OPERATION",
                    "entry_nodes": [
                        {
                            "node_type": "ENTRY",
                            "children": [
                                {
                                    "node_type": "GREATER_THAN",
                                    "children": [
                                        {"node_type": "CONSTANT", "value": 10.0},
                                        {"node_type": "CONSTANT", "value": 5.0}
                                    ]
                                }
                            ]
                        }
                    ],
                    "exit_nodes": []
                }
            ]
        }
    }
    
    settings = StrategySettings(
        default_signal="HOLD",
        position_size=10
    )
    
    engine = StrategyEngine(
        session_id="test_sess",
        strategy_ast=ast,
        settings=settings,
        on_order_intent=on_intent
    )
    
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    candle = CandleEvent(
        event_id="c1",
        session_id="test_sess",
        instrument_token=1,
        symbol="RELIANCE",
        timeframe="1m",
        timestamp=now,
        open=100.0,
        high=105.0,
        low=95.0,
        close=102.0,
        volume=1000
    )
    
    engine.on_candle(candle)
    
    assert len(emitted_intents) == 1
    intent = emitted_intents[0]
    
    assert intent.session_id == "test_sess"
    assert intent.symbol == "RELIANCE"
    assert intent.side == "BUY"
    assert intent.quantity == 10
    assert intent.reason == "ENTRY"
