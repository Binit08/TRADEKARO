"""Pydantic models for the RAG knowledge base."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class KnowledgeDoc(BaseModel):
    """
    Atomic knowledge document representing a single concept (indicator, strategy, term).
    """
    id: str = Field(description="Unique identifier (e.g., 'ind_supertrend')")
    type: str = Field(description="Type of document (e.g., 'indicator', 'term', 'strategy')")
    canonical_name: str = Field(description="The proper, canonical name of the concept")
    aliases: List[str] = Field(default_factory=list, description="Alternative names and common typos")
    maps_to_field: Optional[str] = Field(None, description="Exact-match filtering field (if applicable)")
    embedding_text: str = Field(description="The natural language text that will be embedded")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional structured properties")
