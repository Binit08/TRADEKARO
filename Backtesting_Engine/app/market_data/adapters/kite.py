import os
import logging
from typing import List, Dict, Optional, Callable, Any
import pandas as pd
from datetime import datetime
from kiteconnect import KiteConnect, KiteTicker

from app.data.market_event import MarketEvent
from app.domain.events import TickEvent, CandleEvent
from app.market_data.interfaces import HistoricalDataAdapter, LiveFeedAdapter

logger = logging.getLogger(__name__)

class KiteHistoricalAdapter(HistoricalDataAdapter):
    """Adapter for fetching historical data using Kite Connect."""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.api_key = credentials.get("api_key")
        self.access_token = credentials.get("access_token")
        
        if not self.api_key or not self.access_token:
            raise RuntimeError("Missing Kite API Key or Access Token.")
            
        self.kite = KiteConnect(api_key=self.api_key)
        self.kite.set_access_token(self.access_token)

    def _get_instrument_token(self, symbol: str, market_type: str, expiry: Optional[str] = None) -> int:
        """Helper to resolve symbol to instrument token using Kite instruments dump."""
        # For this refactor, we will keep a simple mock or use the exact same logic as loader.py
        # In production, you would fetch kite.instruments() and cache it.
        # Assuming the caller passes the symbol that can be mapped if we load the CSV.
        # We will replicate the CSV loading logic here.
        df = pd.read_csv("https://api.kite.trade/instruments")
        if market_type == "equity":
            matches = df[(df['tradingsymbol'] == symbol) & (df['exchange'] == 'NSE') & (df['segment'] == 'NSE')]
        else:
            matches = df[(df['name'] == symbol) & (df['exchange'] == 'NFO')]
            if expiry:
                matches = matches[matches['expiry'] == expiry]
                
        if matches.empty:
            raise ValueError(f"Could not find instrument token for {symbol}")
        return int(matches.iloc[0]['instrument_token'])

    def fetch_historical(
        self, 
        symbols: List[str], 
        start_date: str, 
        end_date: str, 
        timeframe: str = "1d",
        market_type: str = "equity",
        expiry: Optional[str] = None,
        warmup_bars: int = 0
    ) -> List[MarketEvent]:
        
        valid_timeframes = {"1m": "minute", "2m": "2minute", "3m": "3minute", "5m": "5minute", "15m": "15minute", "30m": "30minute", "60m": "60minute", "1d": "day"}
        if timeframe not in valid_timeframes:
            raise ValueError(f"Invalid timeframe: {timeframe}. Supported: {list(valid_timeframes.keys())}")
            
        all_events = []
        kite_interval = valid_timeframes[timeframe]
        is_continuous = (market_type == "futures")
        
        for symbol in symbols:
            token = self._get_instrument_token(symbol, market_type, expiry)
            
            fetch_start = pd.to_datetime(start_date)
            if warmup_bars > 0:
                candles_per_day = {
                    "1d": 1, "60m": 6, "30m": 13, "15m": 25,
                    "5m": 75, "3m": 125, "2m": 187, "1m": 375
                }.get(timeframe, 1)
                calendar_days = int((warmup_bars / candles_per_day) * 1.6) + 3
                fetch_start -= pd.Timedelta(days=calendar_days)
                    
            records = self.kite.historical_data(
                instrument_token=token,
                from_date=fetch_start.strftime('%Y-%m-%d %H:%M:%S'),
                to_date=end_date,
                interval=kite_interval,
                continuous=is_continuous,
                oi=True
            )
            
            if not records:
                continue
                
            for r in records:
                # Convert string to tz-aware datetime
                dt = pd.to_datetime(r["date"])
                if dt.tz is None:
                    dt = dt.tz_localize('Asia/Kolkata')
                else:
                    dt = dt.tz_convert('Asia/Kolkata')
                    
                all_events.append(MarketEvent(
                    symbol=symbol,
                    timestamp=dt,
                    open=float(r["open"]),
                    high=float(r["high"]),
                    low=float(r["low"]),
                    close=float(r["close"]),
                    volume=int(r["volume"]),
                    oi=int(r.get("oi", 0))
                ))
                
        return all_events


class KiteLiveFeedAdapter(LiveFeedAdapter):
    """Adapter for Live WebSockets using Kite Ticker."""
    
    def __init__(
        self, 
        credentials: Dict[str, Any],
        symbols: List[str],
        timeframe_minutes: int = 1,
        session_id: str = "default_session",
        warmup_candles: int = 0,
        on_tick: Optional[Callable[[TickEvent], None]] = None,
        on_candle: Optional[Callable[[CandleEvent], None]] = None
    ):
        self.credentials = credentials
        self.api_key = credentials.get("api_key")
        self.access_token = credentials.get("access_token")
        self.symbols = symbols
        self.timeframe_minutes = timeframe_minutes
        self.session_id = session_id
        self.warmup_candles = warmup_candles
        self.on_tick = on_tick
        self.on_candle = on_candle
        
        # In a full implementation, you would resolve symbols to tokens here.
        self.instrument_tokens = [] # Requires mapping
        self.symbol_map = {}
        
        self.kws = KiteTicker(self.api_key, self.access_token)
        self.kws.on_ticks = self._on_ticks
        self.kws.on_connect = self._on_connect
        self.kws.on_close = self._on_close
        self.kws.on_error = self._on_error
        
    def _warmup_historical(self):
        if not self.on_candle or self.warmup_candles <= 0:
            return
            
        logger.info(f"Warming up Kite feed with {self.warmup_candles} candles.")
        try:
            hist_adapter = KiteHistoricalAdapter(self.credentials)
            
            end_date = datetime.now()
            days_needed = max(2, int((self.warmup_candles * self.timeframe_minutes) / 375.0) + 1)
            start_date = end_date - pd.Timedelta(days=days_needed)
            
            # Map minutes to historical adapter timeframe string
            tf_str = f"{self.timeframe_minutes}m"
            if self.timeframe_minutes >= 1440:
                tf_str = "1d"
                
            events = hist_adapter.fetch_historical(
                symbols=self.symbols,
                start_date=start_date.strftime('%Y-%m-%d %H:%M:%S'),
                end_date=end_date.strftime('%Y-%m-%d %H:%M:%S'),
                timeframe=tf_str
            )
            
            for event in events[-self.warmup_candles:]:
                candle = CandleEvent(
                    event_id=f"warmup_{event.symbol}_{event.timestamp.timestamp()}",
                    session_id=self.session_id,
                    instrument_token=0,  # mock
                    symbol=event.symbol,
                    timeframe=tf_str,
                    timestamp=event.timestamp,
                    open=event.open,
                    high=event.high,
                    low=event.low,
                    close=event.close,
                    volume=event.volume,
                    is_warmup=True
                )
                self.on_candle(candle)
        except Exception as e:
            logger.error(f"Kite warmup failed: {e}")

    def start(self):
        self._warmup_historical()
        self.kws.connect(threaded=True)
        
    def stop(self):
        if self.kws:
            self.kws.close()
            
    def _on_ticks(self, ws, ticks):
        for t in ticks:
            if self.on_tick:
                # Emulate TickEvent emission
                pass
                
    def _on_connect(self, ws, response):
        if self.instrument_tokens:
            ws.subscribe(self.instrument_tokens)
            ws.set_mode(ws.MODE_FULL, self.instrument_tokens)
            
    def _on_close(self, ws, code, reason):
        logger.info(f"Kite WS closed: {code} - {reason}")
        
    def _on_error(self, ws, code, reason):
        logger.error(f"Kite WS error: {code} - {reason}")
