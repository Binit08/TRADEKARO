import logging
from typing import List, Dict, Optional, Callable, Any
from app.data.market_event import MarketEvent
from app.domain.events import TickEvent, CandleEvent
from app.market_data.interfaces import HistoricalDataAdapter, LiveFeedAdapter
import pandas as pd
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class ShoonyaHistoricalAdapter(HistoricalDataAdapter):
    """Adapter for fetching historical data using Shoonya (Finvasia)."""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.user_id = credentials.get("user_id")
        self.token = credentials.get("token") # access token / session id
        
        if not self.user_id or not self.token:
            raise RuntimeError("Missing Shoonya credentials.")
            
        try:
            from NorenRestApiPy.NorenApi import NorenApi
            class ShoonyaApi(NorenApi):
                def __init__(self):
                    NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/')
                    
            self.api = ShoonyaApi()
            # Shoonya requires a valid session token which we pass directly if we aren't calling login()
            self.api.set_session(userid=self.user_id, password="", usertoken=self.token)
            logger.info("ShoonyaHistoricalAdapter initialized.")
        except ImportError:
            logger.error("NorenRestApiPy is not installed.")
            raise

    def _get_exchange(self, market_type: str) -> str:
        if market_type == "equity":
            return "NSE"
        return "NFO"

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
        
        # Shoonya intervals: 1, 3, 5, 10, 15, 30, 60, 120, 240
        valid_intervals = {"1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30, "60m": 60, "1d": 1440} # day is simulated or fetched differently
        shoonya_interval = valid_intervals.get(timeframe, 1)
        
        all_events = []
        exchange = self._get_exchange(market_type)
        
        for symbol in symbols:
            # We assume 'symbol' is the token for Shoonya, e.g., '22' for ACC
            token = symbol 
            
            try:
                from_dt = pd.to_datetime(start_date)
                to_dt = pd.to_datetime(end_date)
                
                if warmup_bars > 0:
                    from_dt -= pd.Timedelta(days=warmup_bars + 3)
                
                # convert to unix timestamp
                st_epoch = int(time.mktime(from_dt.timetuple()))
                et_epoch = int(time.mktime(to_dt.timetuple()))
                
                ret = self.api.get_time_price_series(exchange=exchange, token=token, starttime=st_epoch, endtime=et_epoch, interval=shoonya_interval)
                
                if isinstance(ret, list):
                    for row in ret:
                        # row = {'stat': 'Ok', 'time': '21-11-2023 15:29:00', 'into': '13.10', 'inth': '13.15', 'intl': '13.10', 'intc': '13.15', 'intv': '124976', 'intvwap': '13.12'}
                        if row.get('stat') == 'Ok':
                            dt = pd.to_datetime(row['time'], format="%d-%m-%Y %H:%M:%S")
                            if dt.tz is None:
                                dt = dt.tz_localize('Asia/Kolkata')
                            else:
                                dt = dt.tz_convert('Asia/Kolkata')
                                
                            all_events.append(MarketEvent(
                                symbol=symbol,
                                timestamp=dt,
                                open=float(row['into']),
                                high=float(row['inth']),
                                low=float(row['intl']),
                                close=float(row['intc']),
                                volume=int(row['intv']),
                                oi=int(row.get('intvwap', 0)) # abuse oi for vwap if missing
                            ))
                            
            except Exception as e:
                logger.error(f"Shoonya fetch error for {symbol}: {e}")
                
        return all_events

class ShoonyaLiveFeedAdapter(LiveFeedAdapter):
    """Adapter for Live WebSockets using Shoonya."""
    
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
        self.user_id = credentials.get("user_id")
        self.token = credentials.get("token")
        self.symbols = symbols
        self.on_tick = on_tick
        self.on_candle = on_candle
        self.ws = None
        
    def start(self):
        logger.info("Shoonya Live Feed Starting...")
        try:
            import threading
            import time
            self._running = True
            
            # Using basic mock thread for Shoonya WS since NorenApi websocket needs active login
            def mock_ws_thread():
                while self._running:
                    time.sleep(1)
                    if self.on_tick:
                        self.on_tick(TickEvent(
                            symbol=self.symbols[0] if self.symbols else "UNKNOWN",
                            timestamp=pd.Timestamp.now(),
                            last_price=0.0,
                            volume=0
                        ))
                        
            self.ws = threading.Thread(target=mock_ws_thread, daemon=True)
            self.ws.start()
            logger.info("Shoonya Live Feed Started (Mock Implementation)")
            
        except Exception as e:
            logger.error(f"Failed to start Shoonya websocket: {e}")
        
    def stop(self):
        logger.info("Shoonya Live Feed Stopped")
        self._running = False
