import pytest
from app.store.redis_store import RedisStore

def test_redis_store_saves_and_retrieves():
    store = RedisStore()
    session_id = "test_sess"
    
    # Save some data
    store.save_candle(session_id, {"close": 100})
    store.save_candle(session_id, {"close": 101})
    
    store.save_portfolio_update(session_id, {"cash": 10000})
    store.save_portfolio_update(session_id, {"cash": 11000})
    
    # Retrieve
    candles = store.get_all_candles(session_id)
    assert len(candles) == 2
    assert candles[1]["close"] == 101
    
    latest_port = store.get_latest_portfolio_state(session_id)
    assert latest_port["cash"] == 11000
    
    # Clear
    store.clear_session(session_id)
    assert len(store.get_all_candles(session_id)) == 0
    assert store.get_latest_portfolio_state(session_id) is None
