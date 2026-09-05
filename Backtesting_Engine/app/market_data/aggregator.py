"""Candle aggregation engine."""
import uuid
import logging
from typing import Dict, Any, Callable
from app.domain.events import TickEvent, CandleEvent

logger = logging.getLogger(__name__)

class CandleAggregator:
    """Aggregates TickEvents into CandleEvents based on a given timeframe.
    
    This abstracts OHLC tracking away from the WebSocket feed.
    """
    
    def __init__(self, timeframe_minutes: int, on_candle: Callable[[CandleEvent], None]):
        self.timeframe_minutes = timeframe_minutes
        self.on_candle = on_candle
        self._current_candles: Dict[str, dict] = {}
        self._prev_cum_vol: Dict[str, float] = {}
        self._last_emit_time: Dict[str, float] = {}
        
    def on_tick(self, tick: TickEvent) -> None:
        """Process an incoming tick and emit a CandleEvent if the timeframe has elapsed."""
        symbol = tick.symbol
        ltp = tick.last_price
        vol = tick.volume or 0.0
        now = tick.timestamp
        
        prev_vol = self._prev_cum_vol.get(symbol, 0.0)
        vol_delta = max(0.0, vol - prev_vol)
        self._prev_cum_vol[symbol] = vol
        
        if symbol not in self._current_candles:
            self._current_candles[symbol] = {
                "open": ltp,
                "high": ltp,
                "low": ltp,
                "close": ltp,
                "volume": vol_delta,
                "start_time": now
            }
            # Emit in-progress candle
            c = self._current_candles[symbol]
            self.on_candle(CandleEvent(
                event_id=str(uuid.uuid4()),
                session_id=tick.session_id,
                instrument_token=tick.instrument_token,
                symbol=tick.symbol,
                timeframe=f"{self.timeframe_minutes}m",
                timestamp=c["start_time"],
                open=c["open"],
                high=c["high"],
                low=c["low"],
                close=c["close"],
                volume=c["volume"],
                is_completed=False
            ))
        else:
            c = self._current_candles[symbol]
            
            elapsed_seconds = (now - c["start_time"]).total_seconds()
            if elapsed_seconds >= (self.timeframe_minutes * 60):
                # Update the old candle with the boundary tick before closing it
                c["high"] = max(c["high"], ltp)
                c["low"] = min(c["low"], ltp)
                c["close"] = ltp
                c["volume"] += vol_delta

                # Emit the COMPLETED candle
                completed_candle = CandleEvent(
                    event_id=str(uuid.uuid4()),
                    session_id=tick.session_id,
                    instrument_token=tick.instrument_token,
                    symbol=tick.symbol,
                    timeframe=f"{self.timeframe_minutes}m",
                    timestamp=c["start_time"],
                    open=c["open"],
                    high=c["high"],
                    low=c["low"],
                    close=c["close"],
                    volume=c["volume"],
                    is_completed=True
                )
                self.on_candle(completed_candle)
                
                # Reset for next minute bucket, starting with this boundary tick
                self._current_candles[symbol] = {
                    "open": ltp,
                    "high": ltp,
                    "low": ltp,
                    "close": ltp,
                    "volume": vol_delta,
                    "start_time": now
                }
                # Emit new in-progress candle
                new_c = self._current_candles[symbol]
                self.on_candle(CandleEvent(
                    event_id=str(uuid.uuid4()),
                    session_id=tick.session_id,
                    instrument_token=tick.instrument_token,
                    symbol=tick.symbol,
                    timeframe=f"{self.timeframe_minutes}m",
                    timestamp=new_c["start_time"],
                    open=new_c["open"],
                    high=new_c["high"],
                    low=new_c["low"],
                    close=new_c["close"],
                    volume=new_c["volume"],
                    is_completed=False
                ))
            else:
                # Update the current in-progress candle
                c["high"] = max(c["high"], ltp)
                c["low"] = min(c["low"], ltp)
                c["close"] = ltp
                c["volume"] += vol_delta
                
                # Throttle emission of in-progress candles to max 1 per 2 seconds
                import time
                current_time = time.time()
                last_emit = self._last_emit_time.get(symbol, 0)
                if current_time - last_emit >= 2.0:
                    self.on_candle(CandleEvent(
                        event_id=str(uuid.uuid4()),
                        session_id=tick.session_id,
                        instrument_token=tick.instrument_token,
                        symbol=tick.symbol,
                        timeframe=f"{self.timeframe_minutes}m",
                        timestamp=c["start_time"],
                        open=c["open"],
                        high=c["high"],
                        low=c["low"],
                        close=c["close"],
                        volume=c["volume"],
                        is_completed=False
                    ))
                    self._last_emit_time[symbol] = current_time
                

