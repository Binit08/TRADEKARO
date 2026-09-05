import logging
from typing import List, Dict, Optional, Callable, Any
from app.data.market_event import MarketEvent
from app.domain.events import TickEvent, CandleEvent
from app.market_data.interfaces import HistoricalDataAdapter, LiveFeedAdapter
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class UpstoxHistoricalAdapter(HistoricalDataAdapter):
    """Adapter for fetching historical data using Upstox."""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.api_key = credentials.get("api_key")
        self.access_token = credentials.get("access_token")
        
        if not self.access_token:
            raise RuntimeError("Missing Upstox Access Token.")
            
        import upstox_client
        configuration = upstox_client.Configuration()
        configuration.access_token = self.access_token
        self.api_instance = upstox_client.HistoryApi(upstox_client.ApiClient(configuration))
        logger.info("UpstoxHistoricalAdapter initialized.")

    def _get_instrument_key(self, symbol: str, market_type: str) -> str:
        if "|" in symbol:
            return symbol
        if market_type == "equity":
            return f"NSE_EQ|{symbol}"
        return symbol

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
        
        valid_timeframes = {"1m": "1minute", "30m": "30minute", "1d": "day"}
        upstox_interval = valid_timeframes.get(timeframe, "1minute")
        
        all_events = []
        for symbol in symbols:
            inst_key = self._get_instrument_key(symbol, market_type)
            
            try:
                from_dt = pd.to_datetime(start_date)
                
                if warmup_bars > 0:
                    from_dt -= pd.Timedelta(days=warmup_bars + 3)
                    
                fd_str = from_dt.strftime('%Y-%m-%d')
                td_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')
                
                api_response = self.api_instance.get_historical_candle_data1(inst_key, upstox_interval, td_str, fd_str, "2.0")
                
                if hasattr(api_response, 'data') and hasattr(api_response.data, 'candles'):
                    candles = api_response.data.candles
                    for candle in candles:
                        dt = pd.to_datetime(candle[0])
                        if dt.tz is None:
                            dt = dt.tz_localize('Asia/Kolkata')
                        else:
                            dt = dt.tz_convert('Asia/Kolkata')
                            
                        all_events.append(MarketEvent(
                            symbol=symbol,
                            timestamp=dt,
                            open=float(candle[1]),
                            high=float(candle[2]),
                            low=float(candle[3]),
                            close=float(candle[4]),
                            volume=int(candle[5]),
                            oi=int(candle[6]) if len(candle) > 6 else 0
                        ))
            except Exception as e:
                logger.error(f"Upstox fetch error for {symbol}: {e}")
                
        return all_events

class UpstoxLiveFeedAdapter(LiveFeedAdapter):
    """Adapter for Live WebSockets using Upstox."""
    
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
        self.access_token = credentials.get("access_token")
        self.symbols = symbols
        self.on_tick = on_tick
        self.on_candle = on_candle
        self.ws = None
        
    def _get_instrument_key(self, symbol: str) -> str:
        if "|" in symbol:
            return symbol
        return f"NSE_EQ|{symbol}"
        
    def start(self):
        logger.info("Upstox Live Feed Starting...")
        import upstox_client
        
        # Upstox V3 Websocket requires fetching an authorized websocket URL first
        configuration = upstox_client.Configuration()
        configuration.access_token = self.access_token
        
        try:
            # We would normally hit Upstox API to get the websocket URI here
            # api_instance = upstox_client.WebsocketApi(upstox_client.ApiClient(configuration))
            # ws_url = api_instance.get_market_data_feed_authorize().data.authorized_redirect_uri
            
            # For this implementation, we simulate the connection setup
            import threading
            import time
            self._running = True
            
            def mock_ws_thread():
                while self._running:
                    time.sleep(1)
                    # Simulate parsing protobuf data and emitting tick
                    if self.on_tick:
                        self.on_tick(TickEvent(
                            symbol=self.symbols[0] if self.symbols else "UNKNOWN",
                            timestamp=pd.Timestamp.now(),
                            last_price=0.0,
                            volume=0
                        ))
                        
            self.ws = threading.Thread(target=mock_ws_thread, daemon=True)
            self.ws.start()
            logger.info("Upstox Live Feed Started (Mock Implementation)")
            
        except Exception as e:
            logger.error(f"Failed to start Upstox websocket: {e}")
        
    def stop(self):
        logger.info("Upstox Live Feed Stopped")
        self._running = False
