import pytest
from unittest.mock import Mock, patch

from backend.strategy_parser.pipeline.semantic_resolver import SemanticResolver, ResolverResult, ApprovalItem
from backend.strategy_parser.parser.llm_client import LLMClient


@pytest.fixture
def mock_llm_client():
    return Mock(spec=LLMClient)

@patch("backend.strategy_parser.pipeline.semantic_resolver.HybridRetriever")
def test_semantic_resolver_no_ambiguity(mock_retriever, mock_llm_client):
    mock_llm_client.call.return_value = '[]'
    
    resolver = SemanticResolver(mock_llm_client)
    result = resolver.resolve("Buy when RSI > 70")
    
    assert len(result.approval_items) == 0
    mock_llm_client.call.assert_called_once()


@patch("backend.strategy_parser.pipeline.semantic_resolver.HybridRetriever")
def test_semantic_resolver_with_ambiguity(mock_retriever, mock_llm_client):
    # LLM now just extracts the terms
    mock_llm_client.call.return_value = '["bullish"]'
    
    # Mock retriever to return ambiguous candidates
    mock_retriever_instance = mock_retriever.return_value
    mock_retriever_instance.retrieve.return_value = (
        [
            {"canonical_name": "EMA20 > EMA50", "rrf_score": 0.02}, # confidence ~0.6 (assumed)
            {"canonical_name": "Price > 200 EMA", "rrf_score": 0.01}
        ], 
        True
    )
    
    resolver = SemanticResolver(mock_llm_client)
    result = resolver.resolve("Trade when the market is bullish.")
    
    assert len(result.approval_items) == 1
    assert result.approval_items[0].source == "bullish"
    assert result.approval_items[0].type == "assumed"
    assert len(result.approval_items[0].candidates) == 2
    assert result.approval_items[0].candidates[0] == "EMA20 > EMA50"


@patch("backend.strategy_parser.pipeline.semantic_resolver.HybridRetriever")
def test_semantic_resolver_invalid_json(mock_retriever, mock_llm_client):
    mock_llm_client.call.return_value = 'This is not json'
    
    resolver = SemanticResolver(mock_llm_client)
    result = resolver.resolve("Buy when bullish")
    
    # Should fall back to empty list on invalid JSON instead of crashing
    assert len(result.approval_items) == 0
