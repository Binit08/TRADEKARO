"""Live market feed engine.

This module implements `LiveKiteFeed`, a production-oriented
feed engine that connects to the Zerodha Kite WebSocket, receives
real-time ticks, and aggregates them into OHLC `MarketEvent` candles
at specified timeframe boundaries (e.g., 1 minute).
"""
import logging
import time
from datetime import datetime, timezone
from typing import Iterator, Optional, Dict, Any, List, Callable
import queue
import threading

from kiteconnect import KiteTicker
from app.data.market_event import MarketEvent
from app.domain.events import TickEvent, CandleEvent
import uuid

logger = logging.getLogger(__name__)

class LiveKiteFeed:
    """Live WebSocket feed mapping to the HistoricalReplayFeed interface.
    
    Subscribes to KiteTicker, aggregates ticks, and yields `MarketEvent` 
    objects at regular intervals without blocking the main event loop.
    """
    
    def __init__(
        self, 
        api_key: str, 
        access_token: str, 
        instrument_tokens: List[int],
        symbol_map: Dict[int, str],
        timeframe_minutes: int = 1,
        session_id: str = "default_session",
        warmup_candles: int = 100,
        on_tick: Optional[Callable[[TickEvent], None]] = None,
        on_candle: Optional[Callable[[CandleEvent], None]] = None
    ):
        """Initialize the LiveKiteFeed.
        
        Args:
            api_key: User's Kite API Key.
            access_token: User's active Kite Access Token.
            instrument_tokens: List of Kite instrument tokens to subscribe to.
            symbol_map: Dictionary mapping instrument token to readable symbol (e.g. {738561: 'RELIANCE'}).
            timeframe_minutes: The candle aggregation timeframe in minutes.
        """
        self.api_key = api_key
        self.access_token = access_token
        self.instrument_tokens = instrument_tokens
        self.symbol_map = symbol_map
        self.timeframe_minutes = timeframe_minutes
        self.session_id = session_id
        self.warmup_candles = warmup_candles
        self.on_tick = on_tick
        self.on_candle = on_candle
        
        self._ticker = KiteTicker(self.api_key, self.access_token)
        self._setup_ticker()
        
        # Internal state
        self._event_queue: queue.Queue = queue.Queue()
        self._running = False
        self.current_time: Optional[datetime] = None
        self.current_event: Optional[MarketEvent] = None
        
        # Aggregation state
        # Dict[instrument_token, dict(open, high, low, close, volume, start_time)]
        self._current_candles: Dict[int, Dict[str, Any]] = {}
        
    def _setup_ticker(self):
        self._ticker.on_ticks = self._on_ticks
        self._ticker.on_connect = self._on_connect
        self._ticker.on_close = self._on_close
        self._ticker.on_error = self._on_error
        
    def _on_connect(self, ws, response):
        logger.info("LiveKiteFeed connected to WebSocket.")
        ws.subscribe(self.instrument_tokens)
        ws.set_mode(ws.MODE_FULL, self.instrument_tokens)
        
    def _on_close(self, ws, code, reason):
        logger.warning(f"LiveKiteFeed connection closed: {code} - {reason}")
        
    def _on_error(self, ws, code, reason):
        logger.error(f"LiveKiteFeed connection error: {code} - {reason}")

    def _on_ticks(self, ws, ticks):
        """Handle incoming ticks and perform aggregation."""
        now = datetime.now(timezone.utc)
        
        for tick in ticks:
            token = tick.get('instrument_token')
            if token not in self.symbol_map:
                continue
                
            ltp = tick.get('last_price')
            if not ltp:
                continue
                
            vol = tick.get('volume_traded', 0.0)
            
            # Emit TickEvent for Phase 3
            tick_event = TickEvent(
                event_id=str(uuid.uuid4()),
                session_id=self.session_id,
                instrument_token=token,
                symbol=self.symbol_map[token],
                timestamp=now,
                last_price=ltp,
                volume=vol,
                bid=None, # Extract if available in depth
                ask=None
            )
            if self.on_tick:
                self.on_tick(tick_event)
            
            # Init new candle tracking if needed
            if token not in self._current_candles:
                self._current_candles[token] = {
                    "open": ltp,
                    "high": ltp,
                    "low": ltp,
                    "close": ltp,
                    "volume": vol,
                    "start_time": now
                }
            else:
                c = self._current_candles[token]
                c["high"] = max(c["high"], ltp)
                c["low"] = min(c["low"], ltp)
                c["close"] = ltp
                c["volume"] = vol
                
                # Check for candle close boundary
                elapsed_seconds = (now - c["start_time"]).total_seconds()
                if elapsed_seconds >= (self.timeframe_minutes * 60):
                    # Candle is complete! Package and dispatch
                    symbol = self.symbol_map[token]
                    market_event = MarketEvent(
                        symbol=symbol,
                        timestamp=c["start_time"], # Time the candle started
                        open=c["open"],
                        high=c["high"],
                        low=c["low"],
                        close=c["close"],
                        volume=c["volume"]
                    )
                    self._event_queue.put(market_event)
                    
                    # Reset tracker for the next period
                    self._current_candles[token] = {
                        "open": ltp,
                        "high": ltp,
                        "low": ltp,
                        "close": ltp,
                        "volume": vol,
                        "start_time": now
                    }

    def reset(self) -> None:
        """Reset internal queue state. Called by PaperEngine before run."""
        while not self._event_queue.empty():
            self._event_queue.get()
        self.current_time = None
        self.current_event = None

    def start_background(self):
        """Start the WebSocket in a background thread."""
        self._warmup_historical()
        
        self._running = True
        self._ticker.connect(threaded=True)
        
    def _warmup_historical(self):
        """Query historical data to warm up indicators before going live."""
        if not self.on_candle:
            return
            
        try:
            from kiteconnect import KiteConnect
            import datetime
            from app.domain.events import CandleEvent
            
            kite = KiteConnect(api_key=self.api_key)
            kite.set_access_token(self.access_token)
            
            end_date = datetime.datetime.now()
            days_needed = max(2, int((self.warmup_candles * self.timeframe_minutes) / 375.0) + 1)
            start_date = end_date - datetime.timedelta(days=days_needed)
            
            interval = f"{self.timeframe_minutes}minute"
            if self.timeframe_minutes == 1:
                interval = "minute"
                
            for token, symbol in self.symbol_map.items():
                logger.info(f"Warming up indicators for {symbol} ({token})...")
                # Attempt to fetch historical data
                records = kite.historical_data(
                    instrument_token=token,
                    from_date=start_date,
                    to_date=end_date,
                    interval=interval,
                    continuous=False
                )
                
                for r in records:
                    candle = CandleEvent(
                        event_id=str(uuid.uuid4()),
                        session_id=self.session_id,
                        instrument_token=token,
                        symbol=symbol,
                        timeframe=f"{self.timeframe_minutes}m",
                        timestamp=r['date'],
                        open=r['open'],
                        high=r['high'],
                        low=r['low'],
                        close=r['close'],
                        volume=r['volume'],
                        is_warmup=True
                    )
                    self.on_candle(candle)
                
            # Allow components a moment to process the batch before live stream starts
            time.sleep(1.0)
            
        except Exception as e:
            logger.warning(f"Failed to fetch warmup historical data (API error?): {e}. Proceeding without warmup.")

    def stop(self):
        """Stop the WebSocket connection and stream."""
        self._running = False
        if self._ticker:
            self._ticker.close()

    def stream(self) -> Iterator[MarketEvent]:
        """Generator that yields `MarketEvent` as they are aggregated.
        
        Unlike historical feed which iterates a static list, this stream
        blocks and waits for new events to arrive from the WebSocket queue.
        """
        self.start_background()
        
        try:
            while self._running:
                try:
                    # Block for 1 second so we can gracefully check self._running
                    event = self._event_queue.get(timeout=1.0)
                    self.current_event = event
                    self.current_time = event.timestamp
                    yield event
                except queue.Empty:
                    continue
        finally:
            self.stop()
