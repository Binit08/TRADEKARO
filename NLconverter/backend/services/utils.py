def map_symbol(index_or_stock: str, exchange: str) -> str:
    mapping = {
        "NIFTY_50": "NIFTY 50",
        "NIFTY_BANK": "NIFTY BANK",
        "NIFTY_IT": "NIFTY IT",
        "NIFTY_NEXT_50": "NIFTY NEXT 50",
        "SENSEX": "SENSEX",
    }
    if index_or_stock in mapping:
        return mapping[index_or_stock]
    clean = index_or_stock.strip().upper()
    if clean.endswith(".NS") or clean.endswith(".BO"):
        clean = clean[:-3]
    return clean

def map_timeframe(tf: str) -> str:
    mapping = {
        "1min": "1m", "2min": "2m", "5min": "5m", "15min": "15m",
        "30min": "30m", "1hr": "1h", "1d": "1d", "1wk": "1wk", "1mo": "1mo",
    }
    tf_lower = tf.lower()
    if tf_lower not in mapping:
        raise ValueError(f"Unsupported timeframe: {tf}")
    return mapping[tf_lower]

import time
from typing import Optional, Dict

_INSTRUMENT_CACHE: Dict[str, dict] = {}
_INSTRUMENT_CACHE_EXPIRY = 0

def get_instrument_token(kite: 'KiteConnect', symbol: str, exchange: str = "NSE") -> Optional[int]:
    global _INSTRUMENT_CACHE, _INSTRUMENT_CACHE_EXPIRY
    
    # Refresh cache every 24 hours
    now = time.time()
    if not _INSTRUMENT_CACHE or now > _INSTRUMENT_CACHE_EXPIRY:
        try:
            instruments = kite.instruments(exchange)
            _INSTRUMENT_CACHE = {item["tradingsymbol"]: item["instrument_token"] for item in instruments}
            _INSTRUMENT_CACHE_EXPIRY = now + (24 * 3600)
        except Exception as e:
            import logging
            logging.getLogger("nlconverter").error(f"Failed to fetch instruments from Kite: {e}")
            return None
            
    return _INSTRUMENT_CACHE.get(symbol)

