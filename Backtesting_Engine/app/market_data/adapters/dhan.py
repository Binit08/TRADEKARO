import logging
from typing import List, Dict, Optional, Callable, Any
from app.data.market_event import MarketEvent
from app.domain.events import TickEvent, CandleEvent
from app.market_data.interfaces import HistoricalDataAdapter, LiveFeedAdapter
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class DhanHistoricalAdapter(HistoricalDataAdapter):
    """Adapter for fetching historical data using Dhan."""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.client_id = credentials.get("client_id")
        self.access_token = credentials.get("access_token")
        
        if not self.client_id or not self.access_token:
            raise RuntimeError("Missing Dhan Client ID or Access Token.")
            
        from dhanhq import dhanhq
        self.dhan = dhanhq(self.client_id, self.access_token)
        logger.info("DhanHistoricalAdapter initialized.")

    def _get_security_id(self, symbol: str) -> str:
        # Dhan uses internal security IDs (e.g. '1333' for HDFC).
        # We assume symbol is the ID or can be mapped.
        # For this skeleton, we assume the user passed the security ID directly.
        return symbol

    def _get_exchange_segment(self, market_type: str) -> str:
        if market_type == "equity":
            return "NSE_EQ"
        elif market_type == "futures" or market_type == "options":
            return "NSE_FNO"
        return "NSE_EQ"

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
        
        all_events = []
        exchange_seg = self._get_exchange_segment(market_type)
        
        for symbol in symbols:
            security_id = self._get_security_id(symbol)
            try:
                from_dt = pd.to_datetime(start_date)
                to_dt = pd.to_datetime(end_date)
                
                if warmup_bars > 0:
                    from_dt -= pd.Timedelta(days=warmup_bars + 3)
                
                fd_str = from_dt.strftime('%Y-%m-%d')
                td_str = to_dt.strftime('%Y-%m-%d')
                
                if timeframe == "1d":
                    response = self.dhan.historical_daily_data(
                        security_id=security_id,
                        exchange_segment=exchange_seg,
                        instrument_type="EQUITY" if market_type == "equity" else "FUT_STK",
                        expiry_code=0,
                        from_date=fd_str,
                        to_date=td_str
                    )
                else:
                    response = self.dhan.intraday_minute_data(
                        security_id=security_id,
                        exchange_segment=exchange_seg,
                        instrument_type="EQUITY" if market_type == "equity" else "FUT_STK"
                    )
                    
                if response and isinstance(response, dict) and response.get('status') == 'success':
                    data = response.get('data', {})
                    # Dhan returns data in columnar format:
                    # {'start_Time': [...], 'open': [...], 'high': [...], ...}
                    if 'start_Time' in data:
                        times = data['start_Time']
                        opens = data['open']
                        highs = data['high']
                        lows = data['low']
                        closes = data['close']
                        volumes = data['volume']
                        
                        for i in range(len(times)):
                            dt = pd.to_datetime(times[i])
                            if dt.tz is None:
                                dt = dt.tz_localize('Asia/Kolkata')
                            else:
                                dt = dt.tz_convert('Asia/Kolkata')
                                
                            all_events.append(MarketEvent(
                                symbol=symbol,
                                timestamp=dt,
                                open=float(opens[i]),
                                high=float(highs[i]),
                                low=float(lows[i]),
                                close=float(closes[i]),
                                volume=int(volumes[i]),
                                oi=0
                            ))
                            
            except Exception as e:
                logger.error(f"Dhan fetch error for {symbol}: {e}")
                
        return all_events

class DhanLiveFeedAdapter(LiveFeedAdapter):
    """Adapter for Live WebSockets using Dhan."""
    
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
        self.client_id = credentials.get("client_id")
        self.access_token = credentials.get("access_token")
        self.symbols = symbols
        self.on_tick = on_tick
        self.on_candle = on_candle
        self.ws = None
        
    def start(self):
        logger.info("Dhan Live Feed Starting...")
        try:
            import threading
            import time
            from dhanhq import marketfeed
            self._running = True
            
            # Using dhanhq marketfeed boilerplate
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
            logger.info("Dhan Live Feed Started (Mock Implementation)")
            
        except Exception as e:
            logger.error(f"Failed to start Dhan websocket: {e}")
        
    def stop(self):
        logger.info("Dhan Live Feed Stopped")
        self._running = False
