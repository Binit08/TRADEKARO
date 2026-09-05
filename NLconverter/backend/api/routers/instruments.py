import io
import threading
import urllib.request
import pandas as pd
import logging
from fastapi import APIRouter, HTTPException

router = APIRouter()
logger = logging.getLogger("nlconverter")

_cached_instruments = None
_instruments_lock = threading.Lock()

@router.get("/instruments")
def get_instruments():
    global _cached_instruments
    if _cached_instruments is not None:
        return {"status": "ok", "instruments": _cached_instruments}
    
    with _instruments_lock:
        if _cached_instruments is not None:
            return {"status": "ok", "instruments": _cached_instruments}
        
        try:
            url = "https://api.kite.trade/instruments/NSE"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                csv_data = response.read()
            
            df = pd.read_csv(io.BytesIO(csv_data))
            df['label'] = df['name'].fillna(df['tradingsymbol'])
            df['value'] = df['tradingsymbol'].astype(str)
            df['label'] = df['label'].astype(str)
            
            instruments = df[['value', 'label']].to_dict('records')
            _cached_instruments = instruments
            return {"status": "ok", "instruments": _cached_instruments}
        except Exception as e:
            logger.error(f"Failed to fetch instruments: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch instruments from provider")

_cached_futures = None
_futures_lock = threading.Lock()

@router.get("/futures")
def get_futures():
    global _cached_futures
    if _cached_futures is not None:
        return {"status": "ok", "data": _cached_futures}
    
    with _futures_lock:
        if _cached_futures is not None:
            return {"status": "ok", "data": _cached_futures}
        
        try:
            url = "https://api.kite.trade/instruments/NFO"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                csv_data = response.read()
            
            df = pd.read_csv(io.BytesIO(csv_data))
            futs = df[df['instrument_type'].isin(['FUTIDX', 'FUTSTK', 'FUT'])]
            
            futures_data = {}
            for _, row in futs.iterrows():
                name = row['name']
                if pd.isna(name): continue
                
                if name not in futures_data:
                    futures_data[name] = {
                        "name": name,
                        "type": "INDEX" if row['instrument_type'] == 'FUTIDX' else "STOCK",
                        "expiries": []
                    }
                futures_data[name]["expiries"].append({
                    "date": str(row['expiry']),
                    "lot_size": int(row['lot_size']),
                    "tradingsymbol": str(row['tradingsymbol'])
                })
            
            for name in futures_data:
                futures_data[name]["expiries"].sort(key=lambda x: x["date"])
                
            _cached_futures = list(futures_data.values())
            _cached_futures.sort(key=lambda x: x["name"])
            
            return {"status": "ok", "data": _cached_futures}
        except Exception as e:
            logger.error(f"Failed to fetch futures: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch futures from provider")
