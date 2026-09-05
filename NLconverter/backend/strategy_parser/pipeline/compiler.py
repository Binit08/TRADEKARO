from typing import Dict, Any, List

from backend.strategy_parser.parser.strategy_parser import StrategyParser


class StrategyCompiler:
    """
    Wraps the existing StrategyParser.
    Receives original strategy, approved interpretations, and assumptions.
    Must not make new assumptions. Must only compile.
    """

    def __init__(self, parser: StrategyParser):
        self.parser = parser

    def compile(self, strategy_text: str, approved_interpretations: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Injects the approved interpretations into the prompt and compiles to Canonical JSON.
        """
        rag_context = ""
        if approved_interpretations:
            rag_context += "EXPLICIT DEFINITIONS TO USE:\n"
            for item in approved_interpretations:
                source = item.get("source", "")
                resolution = item.get("resolution", "")
                rag_context += f"- Whenever the strategy mentions '{source}', explicitly interpret it as: '{resolution}'\n"

        return self.parser.parse_strategy(strategy_text, rag_context=rag_context)
