import urllib.request
import json
import urllib.parse

data = {
    "text": "Buy when the previous candle is green. Exit at 1% take profit or 1% stop loss.",
    "timeframe": "1d",
    "execution_mode": "next_candle_open",
    "position_size": 100,
    "position_size_type": "percentage",
    "pyramiding": 0,
    "capital": 100000,
    "trade_type": "EQUITY"
}

url = 'http://127.0.0.1:8000/api/v1/convert'
req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode('utf-8'))
    print(json.dumps(result, indent=2))
except Exception as e:
    print('Error:', e)
    if hasattr(e, 'read'):
        print('Response:', e.read().decode('utf-8'))
