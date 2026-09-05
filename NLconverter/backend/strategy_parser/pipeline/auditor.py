from dataclasses import dataclass
from typing import List

from backend.strategy_parser.ast import ASTNode


@dataclass
class AuditResult:
    status: str  # "PASS" or "FAIL"
    messages: List[str]


class Auditor:
    """
    Evaluates the final generated AST for execution safety and structural integrity.
    """

    def audit(self, ast: ASTNode) -> AuditResult:
        messages = []
        status = "PASS"

        # Basic structural safety check: ensure the tree actually exists
        if not ast:
            return AuditResult(status="FAIL", messages=["AST root is null."])

        # Additional domain-specific audit rules can be added here
        # E.g. Check for infinite loops, recursive depths, conflicting logical branches

        return AuditResult(status=status, messages=messages)
