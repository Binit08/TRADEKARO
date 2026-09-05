import json
from dataclasses import dataclass
from typing import List

from backend.strategy_parser.parser.llm_client import LLMClient
from backend.strategy_parser.utils import strip_code_fences
from backend.strategy_parser.rag.retriever import HybridRetriever

@dataclass
class ApprovalItem:
    type: str  # "parsed", "assumed", "unparsed"
    source: str
    candidates: List[str]
    confidence: float
    context: str = "" # Stores the embedded string from RAG if resolved


@dataclass
class ResolverResult:
    approval_items: List[ApprovalItem]


class SemanticResolver:
    """
    Pass 1 of the RAG Architecture.
    Extracts trading jargon from the user's prompt and routes it through the HybridRetriever
    to classify terms into 'parsed', 'assumed', and 'unparsed' states.
    """

    SYSTEM_PROMPT = """
You are a Trading Entity Extractor.
Analyze the user's trading strategy and extract ONLY the technical trading terminology, indicators, chart patterns, execution slang, and market structures.

DO NOT extract regular words, numbers, or logic (like "buy", "sell", "when", "cross-over", "crossover", "positive cross-over", "crosses above", "greater than", "100").
DO extract specific jargon like "RSI", "VWAP", "Double Top", "MIS order", "Head and Shoulders", "Support", "Breakout".

Example 1:
User: "Buy when EMA 20 gives a positive cross-over to EMA 50"
Output: ["EMA"]
(Notice how "positive cross-over", "gives", "to" and "buy" are ignored as logic/words).

Example 2:
User: "If RSI drops below 30 on the 5min chart"
Output: ["RSI"]

Example 3:
User: "Sell if Double Top pattern emerges"
Output: ["Double Top"]
"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.retriever = HybridRetriever()

    def resolve(self, strategy_text: str) -> ResolverResult:
        # Step 1: Extract terms using LLM
        prompt = f"Extract trading terminology from the following strategy:\n\n{strategy_text}"
        
        response_schema = {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        }
        
        response_text = self.llm_client.call(
            prompt, 
            system_prompt=self.SYSTEM_PROMPT,
            response_schema=response_schema
        )

        try:
            extracted_terms = json.loads(response_text)
            if not isinstance(extracted_terms, list):
                extracted_terms = []
        except json.JSONDecodeError:
            extracted_terms = []

        approval_items = []
        
        # Step 2: Query DuckDB RAG for each extracted term
        with self.retriever:
            for term in extracted_terms:
                results, is_confident = self.retriever.retrieve(term, top_n=3)
                
                if not results:
                    # Unparsed: The RAG knows nothing about this term
                    approval_items.append(
                        ApprovalItem(
                            type="unparsed",
                            source=term,
                            candidates=[],
                            confidence=0.0
                        )
                    )
                    continue

                top_result = results[0]
                # Use RRF score to estimate confidence for UI
                # Typically RRF max is around 0.033 with k=60
                # Let's normalize it roughly so 0.033 -> ~0.9
                raw_score = top_result.get("rrf_score", 0.0)
                confidence = min(1.0, raw_score * 30.0) 
                candidate_name = top_result.get("canonical_name", "")
                context_string = top_result.get("embedding_text", "")
                
                # Create candidates list for the UI
                candidates = [res.get("canonical_name", "") for res in results]

                if confidence >= 0.8:
                    # Parsed: High confidence semantic match
                    approval_items.append(
                        ApprovalItem(
                            type="parsed",
                            source=term,
                            candidates=[candidate_name],
                            confidence=confidence,
                            context=context_string
                        )
                    )
                elif confidence >= 0.4:
                    # Assumed: Medium confidence, needs UI confirmation
                    approval_items.append(
                        ApprovalItem(
                            type="assumed",
                            source=term,
                            candidates=candidates,
                            confidence=confidence,
                            context=context_string
                        )
                    )
                else:
                    # Unparsed: Low confidence, basically a guess
                    approval_items.append(
                        ApprovalItem(
                            type="unparsed",
                            source=term,
                            candidates=candidates,
                            confidence=confidence
                        )
                    )

        return ResolverResult(approval_items=approval_items)
