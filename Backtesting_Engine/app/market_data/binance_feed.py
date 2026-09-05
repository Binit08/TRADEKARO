
import logging
import time
import json
import uuid
import queue
import threading
from datetime import datetime, timezone
from typing import Iterator, Optional, Dict, Any, List, Callable
import requests
import websocket

from app.data.market_event import MarketEvent
from app.domain.events import TickEvent, CandleEvent

logger = logging.getLogger(__name__)

class BinanceLiveFeed:
    """Live WebSocket feed using Binance Public API.
    
    Subscribes to Binance @kline_1m stream and yields `MarketEvent`
    objects for crypto symbols (e.g. BTCUSDT) 24/7.
    """
    
    def __init__(
        self, 
        symbols: List[str],
        timeframe_minutes: int = 1,
        session_id: str = "default_session",
        warmup_candles: int = 100,
        on_tick: Optional[Callable[[TickEvent], None]] = None,
        on_candle: Optional[Callable[[CandleEvent], None]] = None
    ):
        self.symbols = [s.lower() for s in symbols]
        self.raw_symbols = symbols
        self.timeframe_minutes = timeframe_minutes
        self.session_id = session_id
        self.warmup_candles = warmup_candles
        self.on_tick = on_tick
        self.on_candle = on_candle
        
        self._ws = None
        self._event_queue = queue.Queue()
        self._running = False
        self.current_time = None
        self.current_event = None
        
        self._intervals = {
            1: "1m",
            3: "3m",
            5: "5m",
            15: "15m",
            30: "30m",
            60: "1h",
            240: "4h",
            1440: "1d"
        }
        self.interval = self._intervals.get(self.timeframe_minutes, "1m")
        
    def reset(self) -> None:
        while not self._event_queue.empty():
            self._event_queue.get()
        self.current_time = None
        self.current_event = None
        
    def start_background(self):
        self._warmup_historical()
        
        self._running = True
        
        # Build Binance WS URL
        streams = "/".join([f"{sym}@kline_{self.interval}" for sym in self.symbols])
        ws_url = f"wss://stream.binance.com:9443/stream?streams={streams}"
        
        self._ws = websocket.WebSocketApp(
            ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        
        self._ws_thread = threading.Thread(target=self._ws.run_forever, daemon=True)
        self._ws_thread.start()
        
    def _on_open(self, ws):
        logger.info(f"BinanceLiveFeed connected to {self.symbols}")
        
    def _on_close(self, ws, close_status_code, close_msg):
        logger.warning(f"BinanceLiveFeed closed: {close_msg}")
        
    def _on_error(self, ws, error):
        logger.error(f"BinanceLiveFeed error: {error}")
        
    def _on_message(self, ws, message):
        data = json.loads(message)
        if "data" in data and "k" in data["data"]:
            kline = data["data"]["k"]
            symbol = kline["s"] # e.g. BTCUSDT
            
            # Emit tick for current price
            ltp = float(kline["c"])
            now = datetime.now(timezone.utc)
            tick_event = TickEvent(
                event_id=str(uuid.uuid4()),
                session_id=self.session_id,
                instrument_token=hash(symbol) % 1000000, # Mock token
                symbol=symbol,
                timestamp=now,
                last_price=ltp,
                volume=float(kline["v"])
            )
            if self.on_tick:
                self.on_tick(tick_event)
                
            # If the kline is closed (completed), emit a MarketEvent
            is_closed = kline["x"]
            if is_closed:
                dt = datetime.fromtimestamp(kline["t"] / 1000.0, tz=timezone.utc)
                market_event = MarketEvent(
                    symbol=symbol,
                    timestamp=dt,
                    open=float(kline["o"]),
                    high=float(kline["h"]),
                    low=float(kline["l"]),
                    close=float(kline["c"]),
                    volume=float(kline["v"])
                )
                self._event_queue.put(market_event)

    def _warmup_historical(self):
        if not self.on_candle or self.warmup_candles <= 0:
            return
            
        logger.info(f"Warming up Binance feed with {self.warmup_candles} candles.")
        for symbol in self.raw_symbols:
            try:
                url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}&interval={self.interval}&limit={self.warmup_candles}"
                res = requests.get(url)
                if res.status_code == 200:
                    klines = res.json()
                    for k in klines:
                        dt = datetime.fromtimestamp(k[0] / 1000.0, tz=timezone.utc)
                        candle = CandleEvent(
                            event_id=str(uuid.uuid4()),
                            session_id=self.session_id,
                            instrument_token=hash(symbol.upper()) % 1000000,
                            symbol=symbol.upper(),
                            timeframe=f"{self.timeframe_minutes}m",
                            timestamp=dt,
                            open=float(k[1]),
                            high=float(k[2]),
                            low=float(k[3]),
                            close=float(k[4]),
                            volume=float(k[5]),
                            is_warmup=True
                        )
                        self.on_candle(candle)
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Binance warmup failed for {symbol}: {e}")

    def stop(self):
        self._running = False
        if self._ws:
            self._ws.close()

    def stream(self) -> Iterator[MarketEvent]:
        self.start_background()
        try:
            while self._running:
                try:
                    event = self._event_queue.get(timeout=1.0)
                    self.current_event = event
                    self.current_time = event.timestamp
                    yield event
                except queue.Empty:
                    continue
        finally:
            self.stop()
