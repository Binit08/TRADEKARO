import math
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.api.server import app

def test_run_backtest_serializes_infinity_and_nan_to_null():
    client = TestClient(app)
    
    from datetime import datetime
    
    mock_metrics = {
        "sharpe_ratio": math.inf,
        "max_drawdown": -math.inf,
        "profit_factor": math.nan,
        "total_return": 0.15
    }
    
    mock_result = {
        "metrics": mock_metrics,
        "trades": [],
        "equity_curve": [{"timestamp": datetime(2023, 1, 1), "equity": 100000.0, "cash": 100000.0, "drawdown_pct": 0.0}],
        "drawdown_curve": [],
        "monthly_returns": [],
        "ohlc_data": []
    }
    
    with patch("app.api.routes.MarketDataLoader.load"), \
         patch("app.api.routes.BacktestEngine.run", return_value=mock_result):
        
        import os
        token = os.getenv("BACKTEST_API_TOKEN", "test_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        request_body = {
            "symbol": "AAPL",
            "start": "2023-01-01",
            "end": "2023-01-03",
            "timeframe": "1d",
            "strategy_ast": {
                "operator": "AND",
                "conditions": [
                    {"left": "EMA", "operator": "<", "right": 102}
                ],
                "signal": "BUY"
            },
            "initial_cash": 100000.0,
            "position_size_type": "percent_equity",
            "position_size": 1.0,
            "commission_rate": 0.0005,
            "slippage_bps": 5.0,
            "allow_short": False,
            "close_on_opposite_signal": True
        }
        
        response = client.post("/api/v1/run_backtest", json=request_body, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["metrics"]["sharpe_ratio"] is None
        assert data["metrics"]["max_drawdown"] is None
        assert data["metrics"]["profit_factor"] is None
        assert data["metrics"]["total_return"] == 0.15
