import pytest
from unittest.mock import Mock

from backend.strategy_parser.pipeline.compiler import StrategyCompiler
from backend.strategy_parser.parser.strategy_parser import StrategyParser


@pytest.fixture
def mock_strategy_parser():
    return Mock(spec=StrategyParser)


def test_compiler_without_interpretations(mock_strategy_parser):
    mock_strategy_parser.parse_strategy.return_value = {"status": "success"}
    
    compiler = StrategyCompiler(mock_strategy_parser)
    result = compiler.compile("Buy when RSI > 70", [])
    
    assert result == {"status": "success"}
    mock_strategy_parser.parse_strategy.assert_called_once_with("Buy when RSI > 70", rag_context="")


def test_compiler_with_interpretations(mock_strategy_parser):
    mock_strategy_parser.parse_strategy.return_value = {"status": "success"}
    
    compiler = StrategyCompiler(mock_strategy_parser)
    interpretations = [
        {"source": "bullish", "resolution": "EMA20 > EMA50"}
    ]
    
    result = compiler.compile("Trade when bullish", interpretations)
    
    assert result == {"status": "success"}
    
    # Check that the interpretation was injected into the rag_context
    called_rag_context = mock_strategy_parser.parse_strategy.call_args[1]["rag_context"]
    assert "EXPLICIT DEFINITIONS TO USE:" in called_rag_context
    assert "Whenever the strategy mentions 'bullish', explicitly interpret it as: 'EMA20 > EMA50'" in called_rag_context
