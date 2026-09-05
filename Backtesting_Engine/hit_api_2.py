import requests
import os
url = "http://127.0.0.1:8002/api/v1/run_paper_trade"
headers = {
    "Authorization": f"Bearer {os.environ.get('BACKTEST_API_TOKEN')}"
}
payload = {
    "symbols": ["AAPL"],
    "timeframe": "1m",
    "strategy_ast": {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "operation_nodes": []
        }
    },
    "instrument_tokens": [12345],
    "symbol_map": {"12345": "AAPL"},
    "initial_cash": 100000.0,
    "position_size_type": "percent_equity",
    "position_size": 1.0,
    "execution_mode": "next_candle_open",
    "broker": {
        "broker_name": "kite",
        "credentials": {"api_key": "x", "access_token": "y"}
    }
}
requests.post(url, json=payload, headers=headers)
