import pytest
from unittest.mock import Mock, patch

from backend.strategy_parser.pipeline.orchestrator import PipelineOrchestrator
from backend.strategy_parser.pipeline.blocker_detector import BlockerDetector, BlockerResult, Blocker
from backend.strategy_parser.pipeline.semantic_resolver import SemanticResolver, ResolverResult, ApprovalItem
from backend.strategy_parser.pipeline.compiler import StrategyCompiler
from backend.strategy_parser.pipeline.schema_validator import SchemaValidator
from backend.strategy_parser.pipeline.ast_generator import ASTGenerator
from backend.strategy_parser.pipeline.ast_validator import ASTValidatorStep
from backend.strategy_parser.pipeline.auditor import Auditor, AuditResult


@pytest.fixture
def orchestrator():
    return PipelineOrchestrator(
        blocker_detector=Mock(spec=BlockerDetector),
        semantic_resolver=Mock(spec=SemanticResolver),
        compiler=Mock(spec=StrategyCompiler),
        schema_validator=Mock(spec=SchemaValidator),
        ast_generator=Mock(spec=ASTGenerator),
        ast_validator=Mock(spec=ASTValidatorStep),
        auditor=Mock(spec=Auditor),
    )


@patch("builtins.input")
def test_orchestrator_clear_path(mock_input, orchestrator):
    # Setup mocks for a perfect run
    orchestrator.blocker_detector.detect.return_value = BlockerResult(status="CLEAR", blockers=[])
    orchestrator.semantic_resolver.resolve.return_value = ResolverResult(approval_items=[])
    orchestrator.compiler.compile.return_value = {"status": "canonical"}
    orchestrator.schema_validator.validate.return_value = (True, [])
    
    mock_ast = Mock()
    orchestrator.ast_generator.generate.return_value = mock_ast
    orchestrator.ast_validator.validate.return_value = (True, [])
    orchestrator.auditor.audit.return_value = AuditResult(status="PASS", messages=[])
    
    # Run
    ast, json_out, status = orchestrator.run("Buy when RSI > 70", "test_id")
    
    # Verify
    assert status == "SUCCESS"
    assert json_out == {"status": "canonical"}
    assert ast == mock_ast
    
    # Ensure no input was requested
    mock_input.assert_not_called()


@patch("builtins.input")
def test_orchestrator_clarification_loop(mock_input, orchestrator):
    # First call to detect returns BLOCKED, second call returns CLEAR
    orchestrator.blocker_detector.detect.side_effect = [
        BlockerResult(status="BLOCKED", blockers=[Blocker(reason="R", question="Q")]),
        BlockerResult(status="CLEAR", blockers=[])
    ]
    
    orchestrator.semantic_resolver.resolve.return_value = ResolverResult(approval_items=[])
    orchestrator.compiler.compile.return_value = {"status": "canonical"}
    orchestrator.schema_validator.validate.return_value = (True, [])
    orchestrator.ast_generator.generate.return_value = Mock()
    orchestrator.ast_validator.validate.return_value = (True, [])
    orchestrator.auditor.audit.return_value = AuditResult(status="PASS", messages=[])
    
    # User provides clarification
    mock_input.return_value = "Here is the clarification"
    
    ast, json_out, status = orchestrator.run("Buy when blocked", "test_id")
    
    assert status == "SUCCESS"
    assert orchestrator.blocker_detector.detect.call_count == 2
    mock_input.assert_called_once()
    
    # Verify the clarified text was passed to the compiler
    compiled_text = orchestrator.compiler.compile.call_args[0][0]
    assert "Here is the clarification" in compiled_text


@patch("builtins.input")
def test_orchestrator_approval_loop(mock_input, orchestrator):
    orchestrator.blocker_detector.detect.return_value = BlockerResult(status="CLEAR", blockers=[])
    
    # Resolver returns an ambiguity
    orchestrator.semantic_resolver.resolve.return_value = ResolverResult(approval_items=[
        ApprovalItem(type="interpretation", source="bullish", candidates=["EMA20 > EMA50"], confidence=0.9)
    ])
    
    orchestrator.compiler.compile.return_value = {"status": "canonical"}
    orchestrator.schema_validator.validate.return_value = (True, [])
    orchestrator.ast_generator.generate.return_value = Mock()
    orchestrator.ast_validator.validate.return_value = (True, [])
    orchestrator.auditor.audit.return_value = AuditResult(status="PASS", messages=[])
    
    # User selects option 1
    mock_input.return_value = "1"
    
    ast, json_out, status = orchestrator.run("Buy when bullish", "test_id")
    
    assert status == "SUCCESS"
    mock_input.assert_called_once()
    
    # Verify the approved interpretation was passed to compiler
    approved_interpretations = orchestrator.compiler.compile.call_args[0][1]
    assert len(approved_interpretations) == 1
    assert approved_interpretations[0]["source"] == "bullish"
    assert approved_interpretations[0]["resolution"] == "EMA20 > EMA50"
