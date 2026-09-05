"""Layer 1: Typo and Variant Normalization using RapidFuzz."""

import re
from typing import List, Dict
from rapidfuzz import process, fuzz

from .models import KnowledgeDoc

class TypoNormalizer:
    """Normalizes typos in prompts to canonical terms using fuzzy matching."""

    def __init__(self, docs: List[KnowledgeDoc], threshold: float = 85.0):
        """
        Initialize the normalizer with a knowledge base.
        
        Args:
            docs: List of KnowledgeDoc objects containing canonical names and aliases.
            threshold: Fuzzy matching score threshold (0-100). Default is 85.0.
        """
        self.threshold = threshold
        self.term_mapping: Dict[str, str] = {}
        
        # Build mapping of all known terms (canonical and aliases) to the canonical name
        for doc in docs:
            canonical = doc.canonical_name.lower()
            self.term_mapping[canonical] = doc.canonical_name
            for alias in doc.aliases:
                self.term_mapping[alias.lower()] = doc.canonical_name
                
        self.known_terms = list(self.term_mapping.keys())

    def normalize(self, prompt: str) -> str:
        """
        Scan the prompt for known terms/aliases (including typos) and replace 
        them with their canonical names if they meet the confidence threshold.
        
        Args:
            prompt: The raw user prompt.
            
        Returns:
            The normalized prompt.
        """
        if not self.known_terms:
            return prompt
            
        # Extract unigrams (words) from the prompt to check for fuzzy matches
        words = re.findall(r'\b\w+\b', prompt)
        normalized_prompt = prompt
        
        for word in words:
            # Skip very short words (less likely to be meaningful technical terms)
            if len(word) <= 3:
                continue
                
            # Perform fuzzy search against known terms
            match = process.extractOne(
                word.lower(),
                self.known_terms,
                scorer=fuzz.ratio,
                score_cutoff=self.threshold
            )
            
            if match:
                best_match_term, score, _ = match
                canonical_name = self.term_mapping[best_match_term]
                
                # Replace the matched word in the prompt with the canonical name
                # using word boundaries to ensure we don't partially replace substrings
                normalized_prompt = re.sub(
                    rf'\b{re.escape(word)}\b', 
                    canonical_name, 
                    normalized_prompt, 
                    flags=re.IGNORECASE
                )
                
        return normalized_prompt
