import logging
import pytest
from app.config.settings import StrategySettings
from app.core.backtest_engine import BacktestEngine
from app.data.loader import MarketDataLoader

def test_direct_initialization_validation():
    # Valid values should pass
    settings = StrategySettings(stop_loss_pct=0.05, take_profit_pct=0.1)
    assert settings.stop_loss_pct == 0.05
    assert settings.take_profit_pct == 0.1

    # Out of bounds value should raise ValueError during initialization
    with pytest.raises(ValueError) as exc:
        StrategySettings(stop_loss_pct=1.5)
    assert "stop_loss_pct must be between 0.0 and 1.0" in str(exc.value)

    # Negative values should raise ValueError during initialization
    with pytest.raises(ValueError) as exc:
        StrategySettings(take_profit_pct=-0.01)
    assert "take_profit_pct must be between 0.0 and 1.0" in str(exc.value)

def test_from_any_validation():
    with pytest.raises(ValueError) as exc:
        StrategySettings.from_any({"stop_loss_pct": 1.05})
    assert "stop_loss_pct must be between 0.0 and 1.0" in str(exc.value)

def test_from_any_logs_warning_on_unknown_keys(caplog):
    with caplog.at_level(logging.WARNING):
        settings = StrategySettings.from_any({
            "stop_loss_pct": 0.05,
            "invalid_typo_key": "some_value"
        })
        assert settings.stop_loss_pct == 0.05
        assert "Filtered out unsupported settings key: 'invalid_typo_key'" in caplog.text

def test_resolve_settings_logs_warning_on_unknown_keys(caplog):
    from app.api.routes import create_backtest_engine
    loader = MarketDataLoader()
    engine = create_backtest_engine(
        initial_cash=100000.0,
        settings=StrategySettings(),
        loader=loader,
    )
    
    with caplog.at_level(logging.WARNING):
        resolved = engine._resolve_settings(
            runtime_settings={
                "stop_loss_pct": 0.02,
                "another_invalid_key": 42
            }
        )
        assert resolved.stop_loss_pct == 0.02
        assert "Filtered out unsupported settings key: 'another_invalid_key'" in caplog.text
