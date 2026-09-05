import pytest
from unittest.mock import Mock, MagicMock

from backend.strategy_parser.pipeline.blocker_detector import BlockerDetector, BlockerResult, Blocker
from backend.strategy_parser.parser.llm_client import LLMClient


@pytest.fixture
def mock_llm_client():
    return Mock(spec=LLMClient)


def test_blocker_detector_clear(mock_llm_client):
    mock_llm_client.call.return_value = '{"status": "CLEAR", "blockers": []}'
    
    detector = BlockerDetector(mock_llm_client)
    result = detector.detect("Buy when RSI > 70")
    
    assert result.status == "CLEAR"
    assert len(result.blockers) == 0
    mock_llm_client.call.assert_called_once()


def test_blocker_detector_blocked(mock_llm_client):
    mock_llm_client.call.return_value = '{"status": "BLOCKED", "blockers": [{"reason": "Custom level unknown.", "question": "What is the custom level?"}]}'
    
    detector = BlockerDetector(mock_llm_client)
    result = detector.detect("Buy when RSI crosses above my custom level.")
    
    assert result.status == "BLOCKED"
    assert len(result.blockers) == 1
    assert result.blockers[0].reason == "Custom level unknown."
    assert result.blockers[0].question == "What is the custom level?"


def test_blocker_detector_invalid_json(mock_llm_client):
    mock_llm_client.call.return_value = 'This is not json'
    
    detector = BlockerDetector(mock_llm_client)
    with pytest.raises(RuntimeError, match="Failed to parse LLM response as JSON"):
        detector.detect("Buy when RSI > 70")
