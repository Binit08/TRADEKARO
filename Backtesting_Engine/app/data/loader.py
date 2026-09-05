"""Historical Market Data Loader.

Loads OHLCV data for backtesting.

.. warning::
    This loader uses Kite Connect API to fetch missing data on the fly.
    Broker credentials (e.g. KITE_API_KEY) must be provided dynamically via the API payload.
"""

from typing import Dict, Iterator, List, Any
import logging
import threading
import pandas as pd
from cachetools import TTLCache
from app.data.market_event import MarketEvent
import os


logger = logging.getLogger(__name__)

# Global in-memory cache for market data (stores up to 100 pandas DataFrames for 1 hour)
_MARKET_DATA_CACHE = TTLCache(maxsize=100, ttl=3600)
_MARKET_DATA_LOCK = threading.Lock()



class MarketDataLoader:
    """Loads and provides historical market data via Zerodha Kite API.

    Attributes:
        data_path: Absolute or relative directory path where CSV files are read or written.
        auto_adjust: Maintained for interface compatibility, not used by Kite.
    """
    _VERSION = "v2_kite"
    
    def __init__(self, data_path: str = "app/market_data", auto_adjust: bool = True):
        self.data_path = data_path
        self.auto_adjust = auto_adjust
        self._df: pd.DataFrame = pd.DataFrame()
        self.dfs: Dict[str, pd.DataFrame] = {}



    def load(self, symbols: List[str], start_date: str, end_date: str, timeframe: str = "1d", market_type: str = "equity", expiry: str = None, warmup_bars: int = 0, broker: Dict[str, Any] = None) -> List[MarketEvent]:
        """Fetch data dynamically using the generic BrokerAdapterFactory and return as MarketEvents."""
        from app.market_data.factory import BrokerAdapterFactory
        import pandas as pd
        
        valid_timeframes = {"1m": "minute", "2m": "2minute", "3m": "3minute", "5m": "5minute", "15m": "15minute", "30m": "30minute", "60m": "60minute", "1d": "day"}
        if timeframe not in valid_timeframes:
            raise ValueError(f"Invalid timeframe: {timeframe}. Supported: {list(valid_timeframes.keys())}")
            
        all_events = []
        self.dfs = {}
        
        # We need a fallback if broker dict isn't provided but legacy env vars are present
        if not broker:
            raise RuntimeError("No broker credentials provided dynamically.")
        
        adapter = BrokerAdapterFactory.get_historical_adapter(broker)
        
        # Note: In a full production implementation, we'd also migrate the RAM caching logic 
        # from the old load method into either the adapter or a caching decorator layer. 
        # For this refactor, we directly fetch and populate dfs for indicators.
        logger.info(f"Downloading data for {symbols} via {broker.get('broker_name')} adapter...")
        
        events = adapter.fetch_historical(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            market_type=market_type,
            expiry=expiry,
            warmup_bars=warmup_bars
        )
        all_events.extend(events)
        
        # Sort all combined events from all symbols chronologically
        all_events.sort(key=lambda x: x.timestamp)
        
        # Populate self.dfs so that indicator calculation works (requires DataFrame)
        # Group events by symbol
        symbol_events = {}
        for ev in all_events:
            symbol_events.setdefault(ev.symbol, []).append({
                "timestamp": ev.timestamp,
                "open": ev.open,
                "high": ev.high,
                "low": ev.low,
                "close": ev.close,
                "volume": ev.volume,
                "oi": ev.oi
            })
            
        for sym, evs in symbol_events.items():
            df = pd.DataFrame(evs)
            self.dfs[sym] = df
            
        return all_events

    def get_data(self) -> Dict[str, pd.DataFrame]:
        """Returns the loaded DataFrames for indicator calculation."""
        return {sym: df.copy() for sym, df in self.dfs.items()}


def fetch_historical(request: dict, out_dir: str) -> dict:
    """Download OHLCV via generic BrokerAdapter and write one .parquet file per symbol under out_dir."""
    from pathlib import Path
    from app.market_data.factory import BrokerAdapterFactory
    import pandas as pd
    
    symbols = request.get("symbols", [])
    start_date = request.get("start")
    end_date = request.get("end")
    interval = request.get("interval", "1d")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    mapping = {}
    
    broker = request.get("broker")
    if not broker:
        raise RuntimeError("No broker credentials provided dynamically.")
            
    adapter = BrokerAdapterFactory.get_historical_adapter(broker)
    
    for symbol in symbols:
        try:
            events = adapter.fetch_historical(
                symbols=[symbol],
                start_date=start_date,
                end_date=end_date,
                timeframe=interval,
                market_type=request.get("market_type", "equity"),
            )
            
            if not events:
                logger.warning(f"No data returned for {symbol}")
                continue

            # Convert events to DataFrame
            data = []
            for ev in events:
                data.append({
                    "timestamp": ev.timestamp,
                    "open": ev.open,
                    "high": ev.high,
                    "low": ev.low,
                    "close": ev.close,
                    "volume": ev.volume,
                    "oi": ev.oi
                })
                
            df = pd.DataFrame(data)
            
            file_path = out_path / f"{symbol}_{interval}_{start_date}_{end_date}_{broker['broker_name']}.parquet"
            df.to_parquet(file_path, index=False)
            mapping[symbol] = str(file_path)
            
        except Exception as e:
            logger.warning(f"Failed to download data for {symbol}: {e}")

    return mapping
