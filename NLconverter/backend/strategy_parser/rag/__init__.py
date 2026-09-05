"""Retrieval-Augmented Generation (RAG) module for financial knowledge."""

import duckdb
import json
from pathlib import Path
from typing import Tuple, List, Optional

from .models import KnowledgeDoc
from .normalizer import TypoNormalizer
from .retriever import HybridRetriever

class RAGSystem:
    """Facade for the RAG system that coordinates normalization and retrieval."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls) -> "RAGSystem":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.retriever = HybridRetriever()
        self.normalizer = self._init_normalizer()
        
    def _init_normalizer(self) -> TypoNormalizer:
        """Load all docs from DuckDB to initialize the TypoNormalizer."""
        if not Path(self.retriever.db_path).exists():
            return TypoNormalizer(docs=[])
            
        conn = duckdb.connect(self.retriever.db_path, read_only=True)
        try:
            results = conn.execute("SELECT id, type, canonical_name, aliases, maps_to_field, embedding_text, metadata FROM knowledge_docs").fetchall()
        except Exception:
            return TypoNormalizer(docs=[])
        finally:
            conn.close()
            
        docs = []
        for row in results:
            docs.append(KnowledgeDoc(
                id=row[0],
                type=row[1],
                canonical_name=row[2],
                aliases=row[3] if row[3] else [],
                maps_to_field=row[4],
                embedding_text=row[5],
                metadata=json.loads(row[6]) if row[6] else {}
            ))
            
        return TypoNormalizer(docs=docs)

    def get_context(self, prompt: str) -> Tuple[str, bool]:
        """
        Normalize the prompt and retrieve relevant context.
        
        Args:
            prompt: Raw user prompt.
            
        Returns:
            Tuple of (formatted context string, is_confident boolean)
        """
        if not Path(self.retriever.db_path).exists():
            return "", False
            
        normalized_prompt = self.normalizer.normalize(prompt)
        results, is_confident = self.retriever.retrieve(normalized_prompt, top_n=3)
        
        if not results:
            return "", False
            
        context_parts = ["Relevant Market Context:"]
        for res in results:
            # Format: - Canonical Name: Definition
            context_parts.append(f"- {res['canonical_name']}: {res['embedding_text']}")
            
        return "\n".join(context_parts), is_confident


def get_rag_context(prompt: str) -> Tuple[str, bool]:
    """
    Main interface to get RAG context.
    
    Args:
        prompt: Raw user prompt.
        
    Returns:
        Tuple of (formatted context string, is_confident boolean).
    """
    system = RAGSystem.get_instance()
    return system.get_context(prompt)
