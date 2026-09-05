import pytest
import os
import time
from unittest.mock import patch, MagicMock
from fastapi import Request, HTTPException
from app.api.models import BacktestRequest
from app.api.routes import check_rate_limit, run_backtest, _RATE_LIMIT_CACHE, TRUSTED_PROXIES, get_client_ip
from pydantic import ValidationError
from datetime import date

# Helper to build valid init kwargs for BacktestRequest
def get_valid_kwargs():
    return {
        "symbol": "AAPL",
        "start": date(2023, 1, 1),
        "end": date(2023, 1, 3),
        "timeframe": "1d",
        "strategy_ast": {
            "operator": "AND",
            "conditions": [
                {"left": "EMA", "operator": "<", "right": 102}
            ],
            "signal": "BUY"
        },
        "initial_cash": 10000.0,
        "position_size_type": "percent_equity",
        "position_size": 0.5,
        "commission_rate": 0.001,
        "slippage_bps": 2.0,
        "allow_short": False,
        "close_on_opposite_signal": True
    }

def test_valid_request_validation():
    # Should validate without error
    kwargs = get_valid_kwargs()
    req = BacktestRequest(**kwargs)
    assert req.symbol == "AAPL"
    assert req.start == date(2023, 1, 1)

def test_invalid_symbol_rejection():
    kwargs = get_valid_kwargs()
    
    kwargs["symbol"] = "A" * 33
    with pytest.raises(ValidationError):
        BacktestRequest(**kwargs)
        
    # Bad characters
    kwargs["symbol"] = "AAPL!!"
    with pytest.raises(ValidationError):
        BacktestRequest(**kwargs)

def test_invalid_dates_rejection():
    kwargs = get_valid_kwargs()
    kwargs["start"] = "not-a-date"
    with pytest.raises(ValidationError):
        BacktestRequest(**kwargs)

def test_out_of_bounds_numbers_rejection():
    # initial_cash <= 0
    kwargs = get_valid_kwargs()
    kwargs["initial_cash"] = 0
    with pytest.raises(ValidationError):
        BacktestRequest(**kwargs)
        
    # initial_cash > 1e10
    kwargs = get_valid_kwargs()
    kwargs["initial_cash"] = 2e10
    with pytest.raises(ValidationError):
        BacktestRequest(**kwargs)

    # commission_rate > 1
    kwargs = get_valid_kwargs()
    kwargs["commission_rate"] = 1.1
    with pytest.raises(ValidationError):
        BacktestRequest(**kwargs)

    # slippage_bps > 10,000
    kwargs = get_valid_kwargs()
    kwargs["slippage_bps"] = 10001.0
    with pytest.raises(ValidationError):
        BacktestRequest(**kwargs)

def test_strategy_ast_size_limit_rejection():
    kwargs = get_valid_kwargs()
    large_ast = {"operator": "AND", "conditions": []}
    for i in range(12000):
        large_ast["conditions"].append({"left": "EMA", "operator": "<", "right": i})
    kwargs["strategy_ast"] = large_ast
    with pytest.raises(ValidationError) as exc_info:
        BacktestRequest(**kwargs)
    assert "strategy_ast exceeds maximum JSON size of 256 KB" in str(exc_info.value)

def test_strategy_ast_schema_rejection():
    kwargs = get_valid_kwargs()
    kwargs["strategy_ast"] = {"invalid_key": "val"}
    with pytest.raises(ValidationError) as exc_info:
        BacktestRequest(**kwargs)
    assert "validation failed against JSON schema" in str(exc_info.value)

def test_rate_limiter_limit_and_reset():
    _RATE_LIMIT_CACHE.clear()
    
    # Mock Request
    mock_request = MagicMock(spec=Request)
    mock_request.client.host = "192.168.1.100"
    mock_request.headers = {}
    
    # Call 10 times successfully
    for _ in range(10):
        check_rate_limit(mock_request)
        
    # 11th call must raise HTTPException 429
    with pytest.raises(HTTPException) as exc_info:
        check_rate_limit(mock_request)
    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "Too many requests"

def test_trusted_proxy_header():
    _RATE_LIMIT_CACHE.clear()
    
    with patch("app.api.routes.TRUSTED_PROXIES", ["127.0.0.1"]):
        # Direct connection from trusted proxy, X-Forwarded-For present
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"X-Forwarded-For": "203.0.113.19"}
        
        assert get_client_ip(mock_request) == "203.0.113.19"

        # Direct connection from untrusted IP, X-Forwarded-For present (should ignore)
        mock_request_untrusted = MagicMock(spec=Request)
        mock_request_untrusted.client.host = "198.51.100.1"
        mock_request_untrusted.headers = {"X-Forwarded-For": "203.0.113.19"}
        assert get_client_ip(mock_request_untrusted) == "198.51.100.1"

def test_generic_exception_mapping():
    kwargs = get_valid_kwargs()
    req = BacktestRequest(**kwargs)
    
    with patch("app.core.backtest_engine.BacktestEngine.run") as mock_run:
        # Mock ValueError
        mock_run.side_effect = ValueError("Sensitive database query error details")
        with pytest.raises(HTTPException) as exc_info:
            run_backtest(req)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Configuration Error: Sensitive database query error details"
        
        # Mock RuntimeError
        mock_run.side_effect = RuntimeError("Kite API rate limited or internet down")
        with pytest.raises(HTTPException) as exc_info:
            run_backtest(req)
        assert exc_info.value.status_code == 502
        assert exc_info.value.detail == "Engine Error: Kite API rate limited or internet down"

def test_timeout_execution():
    from app.core.backtest_engine import BacktestEngine
    from app.data.market_event import MarketEvent
    import threading
    import datetime
    import time
    from unittest.mock import MagicMock
    
    # We want a feed that loops forever and yields candles, sleeping briefly to simulate execution time
    class SlowReplayFeed:
        def __init__(self, events):
            self.events = events
            self.is_exited = False
        def reset(self):
            pass
        def stream(self):
            try:
                while True:
                    yield MarketEvent(symbol="AAPL", timestamp=datetime.datetime(2023, 1, 1), open=100.0, high=101.0, low=99.0, close=100.0, volume=1000)
                    time.sleep(0.01)
            finally:
                self.is_exited = True

    # Let's mock a loader that returns one dummy event
    dummy_event = MarketEvent(symbol="AAPL", timestamp=datetime.datetime(2023, 1, 1), open=100.0, high=101.0, low=99.0, close=100.0, volume=1000)
    mock_loader = MagicMock()
    mock_loader.load.return_value = [dummy_event]

    # Create the backtest engine
    engine = BacktestEngine(
        loader=mock_loader,
        feed=SlowReplayFeed,
        indicator=MagicMock(),
        signal=MagicMock(),
        execution=MagicMock(),
        portfolio=MagicMock(),
        metrics=MagicMock()
    )
    
    # We configure a very short timeout
    engine.timeout_seconds = 0.05
    
    # Running should raise TimeoutError
    with pytest.raises(TimeoutError, match="Backtest execution timed out after 0.05 seconds"):
        engine.run(
            symbols=["AAPL"],
            start="2023-01-01",
            end="2023-01-03",
            timeframe="1d",
            strategy_ast={"left": 1, "operator": ">", "right": 0}
        )
    
    # Give the thread 1 second to cooperatively exit
    time.sleep(1.0)
    
    # Check that any new threads spawned by the ThreadPoolExecutor are no longer active/running.
    # When the ThreadPoolExecutor exits its block, it joins/shuts down its worker threads.
    current_threads = threading.enumerate()
    for t in current_threads:
        if "ThreadPoolExecutor" in t.name:
            assert not t.is_alive()



def test_drawdown_consistency():
    kwargs = get_valid_kwargs()
    req = BacktestRequest(**kwargs)
    
    test_cases = [
        (10000.0, [10000.0, 11000.0, 12000.0, 13000.0], 0.0),
        (10000.0, [10000.0, 12000.0, 9000.0, 11000.0], 25.0),
        (10000.0, [10000.0, 15000.0, 12000.0, 16000.0, 14000.0], 20.0)
    ]
    
    for initial_cash, eq_values, expected_max_dd in test_cases:
        import datetime
        start_date = datetime.datetime(2023, 1, 1)
        
        equity_curve_records = []
        running_max = initial_cash
        for idx, eq in enumerate(eq_values):
            if eq > running_max:
                running_max = eq
            dd = ((running_max - eq) / running_max) * 100.0 if running_max > 0 else 0.0
            
            equity_curve_records.append({
                "step": idx,
                "timestamp": start_date + datetime.timedelta(days=idx),
                "equity": float(eq),
                "cash": float(initial_cash),
                "drawdown_pct": float(dd)
            })
            
        from app.metrics.metrics_engine import MetricsEngine
        m_engine = MetricsEngine()
        metrics_out = m_engine.compute(
            equity_history=eq_values,
            trade_history=[],
            equity_curve=equity_curve_records
        )
        
        assert metrics_out["max_drawdown"] == pytest.approx(expected_max_dd)
        
        req.initial_cash = initial_cash
        with patch("app.core.backtest_engine.BacktestEngine.run") as mock_run:
            mock_run.return_value = {
                "portfolio": {"cash": initial_cash, "equity": eq_values[-1], "positions": {}},
                "metrics": metrics_out,
                "trades": [],
                "closed_trades": [],
                "open_trades": [],
                "equity_curve": equity_curve_records
            }
            
            res_response = run_backtest(req)
            
            max_drawdown_metrics = res_response.metrics["max_drawdown"]
            drawdown_curve = res_response.drawdown_curve
            
            max_drawdown_curve = max(-x["drawdownPct"] for x in drawdown_curve) if drawdown_curve else 0.0
            
            assert max_drawdown_metrics == pytest.approx(max_drawdown_curve)
            assert max_drawdown_metrics == pytest.approx(expected_max_dd)


def test_metrics_engine_non_positive_initial_equity():
    from app.metrics.metrics_engine import MetricsEngine
    m_engine = MetricsEngine()
    with pytest.raises(ValueError, match="Initial equity must be greater than zero"):
        m_engine.compute([0.0, 100.0], [])
    with pytest.raises(ValueError, match="Initial equity must be greater than zero"):
        m_engine.compute([-10.0, 100.0], [])


def test_api_serialization_open_trades():
    kwargs = get_valid_kwargs()
    req = BacktestRequest(**kwargs)
    
    from app.execution.trade import Trade
    import datetime
    
    def mock_run_impl(self, symbols, start, end, timeframe, strategy_ast, strategy_settings=None, cancel_event=None, broker=None):
        open_trade = Trade(
            symbol="AAPL",
            side="BUY",
            entry_price=150.0,
            qty=10.0,
            entry_time=datetime.datetime(2023, 1, 1, 10, 0),
            status="OPEN",
            fees=5.0,
            slippage=0.0,
            pnl=None,  # Open trades should have pnl=None/unrealized
            original_entry_price=145.0,
            lifecycle_first_entry_price=145.0
        )
        self.portfolio.trade_history.append(open_trade)
        return {
            "portfolio": {"cash": 10000.0, "equity": 10000.0, "positions": {}},
            "metrics": {
                "return_pct": 0.0,
                "win_rate": 0.0,
                "average_win": 0.0,
                "average_loss": 0.0,
                "profit_factor": 0.0,
                "max_drawdown": 0.0,
                "total_trades": 1,
                "open_trades": 1,
                "closed_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "break_even_trades": 0,
                "net_pnl": 0.0,
                "realized_pnl": 0.0,
                "unrealized_pnl": 0.0,
                "accounting_drift": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "longest_win_streak": 0,
                "longest_loss_streak": 0,
                "warnings": []
            },
            "trades": [open_trade],
            "closed_trades": [],
            "open_trades": [open_trade],
            "equity_curve": [{"timestamp": datetime.datetime(2023, 1, 1), "equity": 10000.0, "cash": 10000.0, "drawdown_pct": 0.0}],
            "warnings": []
        }

    with patch("app.core.backtest_engine.BacktestEngine.run", mock_run_impl):
        res_response = run_backtest(req)
        
        # Verify JSON serialization works (e.g., via FastAPI/Pydantic dict dump)
        dumped = res_response.model_dump()
        assert "trades" in dumped
        assert len(dumped["trades"]) == 1
        
        t_serialized = dumped["trades"][0]
        assert t_serialized["status"] == "OPEN"
        assert t_serialized["exit_time"] is None
        assert t_serialized["exit_price"] is None
        assert t_serialized["pnl"] is None
        assert t_serialized["avg_entry_price"] == 150.0
        assert t_serialized["original_entry_price"] == 145.0


def test_create_backtest_engine_factory():
    from app.api.routes import create_backtest_engine
    from app.config.settings import StrategySettings
    from app.data.loader import MarketDataLoader
    
    settings = StrategySettings()
    loader = MarketDataLoader()
    
    engine1 = create_backtest_engine(100000.0, settings, loader)
    engine2 = create_backtest_engine(100000.0, settings, loader)
    
    # Assert distinct instances
    assert engine1 is not engine2
    # Assert distinct subcomponents
    assert engine1.portfolio is not engine2.portfolio
    assert engine1.signal is not engine2.signal
    assert engine1.metrics is not engine2.metrics


def test_ast_recursion_depth_limit():
    from app.ast.loader import StrategyLoader, ASTLoadError
    from app.core.backtest_engine import BacktestEngine
    
    # Create deeply nested AST (depth > 64)
    deep_node = {"node_type": "CONSTANT", "value": 1.0}
    for _ in range(70):
        deep_node = {
            "node_type": "AND",
            "children": [deep_node]
        }
        
    ast_json = {
        "schema_version": "1.0.0",
        "execution_context": {
            "symbol": "AAPL",
            "timeframe": "1D",
            "start_date": "2020-01-01",
            "end_date": "2025-01-01",
            "capital": 100000.0,
            "position_side": "LONG"
        },
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "strategy_id": "deep_ast",
            "operation_nodes": [
                {
                    "node_type": "OPERATION",
                    "entry_nodes": [
                        {
                            "node_type": "ENTRY",
                            "children": [deep_node]
                        }
                    ],
                    "exit_nodes": []
                }
            ]
        }
    }
    
    # 1. Verify StrategyLoader rejects it
    loader = StrategyLoader()
    with pytest.raises(ASTLoadError) as exc_info:
        loader.load_from_json(ast_json)
    assert "AST too deep" in str(exc_info.value)
    
    # 2. Verify IndicatorExtractor rejects it in config extraction
    from app.ast.indicator_extractor import IndicatorExtractor
    with pytest.raises(ValueError, match="AST too deep"):
        IndicatorExtractor.gather_indicator_configs(ast_json, [])


def test_ast_node_count_limit():
    from app.ast.loader import StrategyLoader, ASTLoadError
    from app.core.backtest_engine import BacktestEngine
    
    # Create a wide/large AST with > 10,000 nodes
    large_children = [{"node_type": "CONSTANT", "value": 1.0} for _ in range(10005)]
    large_node = {
        "node_type": "AND",
        "children": large_children
    }
    
    ast_json = {
        "schema_version": "1.0.0",
        "execution_context": {
            "symbol": "AAPL",
            "timeframe": "1D",
            "start_date": "2020-01-01",
            "end_date": "2025-01-01",
            "capital": 100000.0,
            "position_side": "LONG"
        },
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "strategy_id": "large_ast",
            "operation_nodes": [
                {
                    "node_type": "OPERATION",
                    "entry_nodes": [
                        {
                            "node_type": "ENTRY",
                            "children": [large_node]
                        }
                    ],
                    "exit_nodes": []
                }
            ]
        }
    }
    
    # 1. Verify StrategyLoader rejects it
    loader = StrategyLoader()
    with pytest.raises(ASTLoadError) as exc_info:
        loader.load_from_json(ast_json)
    assert "AST has too many nodes" in str(exc_info.value)
    
    # 2. Verify IndicatorExtractor rejects it in config extraction
    from app.ast.indicator_extractor import IndicatorExtractor
    with pytest.raises(ValueError, match="AST has too many nodes"):
        IndicatorExtractor.gather_indicator_configs(ast_json, [])



