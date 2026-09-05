import os
import pytest
from fastapi.testclient import TestClient

# Mock environment variable before loading the app
os.environ["API_KEY"] = "test-api-key"

from backend.main import app
from backend.api.deps import get_current_user
from backend.db.database import get_db
from backend.api.dependencies import verify_api_key
from backend.api.schemas import SCHEMA_CONFIG, MarketType
from backend.strategy_parser.schemas import *

# Override get_db to yield a MagicMock
def override_get_db():
    from unittest.mock import MagicMock
    yield MagicMock()

def override_get_current_user():
    from backend.db.models import User
    return User(id="test_user", email="test@example.com")

def override_verify_api_key():
    return "test-api-key"

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[verify_api_key] = override_verify_api_key

client = TestClient(app)

HEADERS = {
    "X-API-Key": "test-api-key",
    "Authorization": "Bearer test-api-key",
    "Content-Type": "application/json"
}

def test_invalid_market_type():
    payload = {
        "prompt": "Buy when RSI is > 30",
        "market_type": "invalid_type",
        "execution_context": {}
    }
    response = client.post("/api/strategy", json=payload, headers=HEADERS)
    assert response.status_code == 422
    assert "market_type" in response.text
    assert "Input should be 'equity' or 'futures'" in response.text

from unittest.mock import patch

@patch("backend.services.strategy_service.StrategyParser")
@patch("backend.services.strategy_service.StrategyCompiler")
@patch("backend.services.strategy_service.SemanticResolver")
def test_valid_futures_context_schema_loading(mock_semantic, mock_compiler, mock_parser):

    # Mock SemanticResolver
    mock_semantic_instance = mock_semantic.return_value
    mock_semantic_instance.resolve.return_value.approval_items = []
    
    # Mock StrategyCompiler to avoid actual compilation logic during this test
    mock_compiler_instance = mock_compiler.return_value
    mock_compiler_instance.compile.return_value = {
        "signals": {"indicators": []},
        "operation": [{"entry": [], "exit": []}],
        "risk": {"stop_loss": {}, "take_profit": {}, "trailing_stop": {}, "risk_reward": {}}
    }
    
    payload = {
        "prompt": "Buy when RSI is > 30",
        "market_type": "futures",
        "execution_context": {
            "universe": {
                "index": "NIFTY_50",
                "exchange": "NSE",
                "asset_class": "futures"
            },
            "timeframe": "1m",
            "capital_per_trade": {
                "amount": 1000,
                "currency": "INR"
            },
            "position_side": "LONG",
            "order_type": "LIMIT",
            "max_concurrent_positions": 1,
            "future_contract": {
                "underlying": "NIFTY_50",
                "expiry": "2026-06-08",
                "lot_size": 10,
                "margin": 0
            }
        }
    }
    
    response = client.post("/api/strategy", json=payload, headers=HEADERS)
    
    assert response.status_code == 200, response.text
    
    # Verify futures schema was used
    expected_path = SCHEMA_CONFIG[MarketType.FUTURES]["strategy"]
    mock_parser.assert_called_with(strategy_schema_path=expected_path)

def test_invalid_futures_context():
    payload = {
        "prompt": "Buy when RSI is > 30",
        "market_type": "futures",
        "execution_context": {
            "universe": {
                "index": "INVALID_INDEX", # Fails validation
                "exchange": "NSE",
                "asset_class": "futures"
            },
            "timeframe": "1m",
            "capital_per_trade": {
                "amount": -1000, # Invalid amount
                "currency": "INR"
            },
            "position_side": "LONG",
            "order_type": "MARKET",
            "max_concurrent_positions": 1
        }
    }
    
    response = client.post("/api/strategy", json=payload, headers=HEADERS)
    assert response.status_code == 422
    assert "Execution context validation failed" in response.text
