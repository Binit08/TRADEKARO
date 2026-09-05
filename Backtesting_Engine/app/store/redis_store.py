"""Hot state store for paper trading sessions.

This simulates a Redis-backed store to decouple frontend state queries
from the background daemon threads running the engine.
"""
import json
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class RedisStore:
    """In-memory implementation of a Redis-like hot store (Phase 10).
    
    Provides isolated storage for session events, candles, and portfolio state.
    """
    
    def __init__(self):
        # We use a lock for thread safety since we're simulating Redis in-memory
        self._lock = threading.Lock()
        
        # Simulated Redis Keyspaces
        self._ticks: Dict[str, List[Any]] = defaultdict(list)
        self._candles: Dict[str, List[Any]] = defaultdict(list)
        self._portfolio_updates: Dict[str, List[Any]] = defaultdict(list)
        self._position_updates: Dict[str, List[Any]] = defaultdict(list)
        self._order_fills: Dict[str, List[Any]] = defaultdict(list)
        self._session_status: Dict[str, str] = {}
        self._notifiers: Dict[str, List[Any]] = defaultdict(list)

    def register_notifier(self, session_id: str, loop: Any, event: Any) -> None:
        with self._lock:
            self._notifiers[session_id].append((loop, event))

    def unregister_notifier(self, session_id: str, loop: Any, event: Any) -> None:
        with self._lock:
            if (loop, event) in self._notifiers[session_id]:
                self._notifiers[session_id].remove((loop, event))

    def _notify(self, session_id: str) -> None:
        # Call this without holding the lock if possible, or while holding it.
        # But we must not block.
        for loop, event in self._notifiers.get(session_id, []):
            try:
                loop.call_soon_threadsafe(event.set)
            except Exception as e:
                logger.error(f"Failed to notify websocket for {session_id}: {e}")
        
    def save_tick(self, session_id: str, tick: Any) -> None:
        """Save a TickEvent."""
        with self._lock:
            self._ticks[session_id].append(tick)
            # In a real Redis, we'd LTRIM to keep max size (e.g. 1000)
            if len(self._ticks[session_id]) > 5000:
                self._ticks[session_id].pop(0)

    def save_candle(self, session_id: str, candle: Any) -> None:
        """Save a CandleEvent."""
        with self._lock:
            def _get_ts(item):
                return getattr(item, "timestamp", item.get("timestamp") if isinstance(item, dict) else None)
                
            last_ts = _get_ts(self._candles[session_id][-1]) if self._candles[session_id] else None
            new_ts = _get_ts(candle)
            
            # If the last candle has the exact same timestamp, replace it (in-progress updates)
            if self._candles[session_id] and last_ts is not None and last_ts == new_ts:
                self._candles[session_id][-1] = candle
            else:
                self._candles[session_id].append(candle)
        self._notify(session_id)
            
    def save_portfolio_update(self, session_id: str, update: Any) -> None:
        """Save a PortfolioUpdateEvent (acts as the latest MTM state)."""
        with self._lock:
            self._portfolio_updates[session_id].append(update)
        self._notify(session_id)
            
    def save_position_update(self, session_id: str, update: Any) -> None:
        """Save a PositionUpdateEvent."""
        with self._lock:
            self._position_updates[session_id].append(update)
        self._notify(session_id)
            
    def save_order_fill(self, session_id: str, fill: Any) -> None:
        """Save an OrderFill."""
        with self._lock:
            self._order_fills[session_id].append(fill)
        self._notify(session_id)
            
    def set_session_status(self, session_id: str, status: str) -> None:
        with self._lock:
            self._session_status[session_id] = status
            
    def get_latest_portfolio_state(self, session_id: str) -> Optional[Any]:
        """Fetch the most recent portfolio state for the session."""
        with self._lock:
            updates = self._portfolio_updates.get(session_id, [])
            if not updates:
                return None
            return updates[-1]
            
    def get_all_candles(self, session_id: str) -> List[Any]:
        """Fetch all candles for rendering a chart."""
        with self._lock:
            return list(self._candles.get(session_id, []))
            
    def get_all_fills(self, session_id: str) -> List[Any]:
        """Fetch all executed fills for a session."""
        with self._lock:
            return list(self._order_fills.get(session_id, []))
            
    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """Aggregate history for frontend consumption (matches legacy payload)."""
        with self._lock:
            # We recreate the legacy `history` list of dicts for backward compatibility
            # In a real system, the frontend would query REST endpoints mapped to Redis.
            
            # This is a simplified mock of the frontend's expected output
            # which we will refine when wiring up the WebSocket in Phase 13.
            return {
                "candles": len(self._candles.get(session_id, [])),
                "fills": len(self._order_fills.get(session_id, [])),
                "portfolio_updates": len(self._portfolio_updates.get(session_id, []))
            }
            
    def clear_session(self, session_id: str) -> None:
        """Purge all data for a given session."""
        with self._lock:
            self._ticks.pop(session_id, None)
            self._candles.pop(session_id, None)
            self._portfolio_updates.pop(session_id, None)
            self._position_updates.pop(session_id, None)
            self._order_fills.pop(session_id, None)
            self._session_status.pop(session_id, None)

# Global singleton to act as our "Redis connection"
redis_store = RedisStore()
