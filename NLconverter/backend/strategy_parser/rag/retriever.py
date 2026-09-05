"""Layer 2 & 3: Hybrid Retrieval and Confidence Gating."""

import duckdb
from typing import List, Tuple, Dict, Any
from pathlib import Path

from .embedding import GeminiEmbeddingClient

class HybridRetriever:
    """Retrieves relevant knowledge docs using dense (VSS) and sparse (FTS) search."""

    def __init__(self, db_path: str = None, rrf_k: int = 60, confidence_threshold: float = 0.03):
        """
        Initialize the retriever.
        
        Args:
            db_path: Path to the DuckDB database.
            rrf_k: The 'k' constant for Reciprocal Rank Fusion.
            confidence_threshold: Minimum RRF score required to be 'confident'.
        """
        if db_path is None:
            # Default to backend/data/knowledge_base.duckdb
            backend_dir = Path(__file__).resolve().parent.parent.parent
            self.db_path = str(backend_dir / "data" / "knowledge_base.duckdb")
        else:
            self.db_path = db_path
            
        self.rrf_k = rrf_k
        self.confidence_threshold = confidence_threshold
        self.embedding_client = GeminiEmbeddingClient()
        
    def load_embedding_model(self):
        self.embedding_client.load_model()
        
    def unload_embedding_model(self):
        self.embedding_client.unload_model()
        
    def __enter__(self):
        self.load_embedding_model()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unload_embedding_model()
        
    def retrieve(self, query: str, top_n: int = 3) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Perform a hybrid search using RRF and apply confidence gating.
        
        Args:
            query: The normalized user prompt.
            top_n: Number of documents to return.
            
        Returns:
            Tuple of (list of retrieved document dicts, boolean indicating confidence)
        """
        if not Path(self.db_path).exists():
            return [], False
            
        # 1. Generate query embedding
        try:
            query_vec = self.embedding_client.embed_text(query)
        except Exception as e:
            print(f"Warning: Failed to generate query embedding: {e}")
            return [], False
            
        # 2. Connect to DB and perform searches
        conn = duckdb.connect(self.db_path, read_only=True)
        try:
            try:
                conn.execute("LOAD vss;")
            except Exception:
                conn.execute("INSTALL vss;")
                conn.execute("LOAD vss;")

            try:
                conn.execute("LOAD fts;")
            except Exception:
                conn.execute("INSTALL fts;")
                conn.execute("LOAD fts;")
            
            # Dense Search (VSS)
            # We cast the query_vec to FLOAT[3072] for gemini-embedding-001
            dense_results = conn.execute("""
                SELECT id, array_distance(vec, ?::FLOAT[3072]) as dist
                FROM knowledge_docs
                ORDER BY dist ASC
                LIMIT 20
            """, (query_vec,)).fetchall()
            
            # Sparse Search (Fallback to ILIKE due to DuckDB FTS persistence issues)
            sparse_query = f"%{query}%"
            sparse_results = conn.execute("""
                SELECT id, 
                (CASE WHEN embedding_text ILIKE ? THEN 1.0 ELSE 0.0 END) + 
                (CASE WHEN canonical_name ILIKE ? THEN 2.0 ELSE 0.0 END) AS score
                FROM knowledge_docs
                WHERE score > 0
                ORDER BY score DESC
                LIMIT 20
            """, (sparse_query, sparse_query)).fetchall()
            
            # Fetch all docs to return metadata later
            all_docs = conn.execute("""
                SELECT id, canonical_name, embedding_text, metadata 
                FROM knowledge_docs
            """).fetchall()
            
        finally:
            conn.close()
            
        doc_map = {row[0]: {"canonical_name": row[1], "embedding_text": row[2], "metadata": row[3]} for row in all_docs}
        
        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        
        for rank, (doc_id, _dist) in enumerate(dense_results, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (self.rrf_k + rank))
            
        for rank, (doc_id, _score) in enumerate(sparse_results, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (self.rrf_k + rank))
            
        if not rrf_scores:
            return [], False
            
        # Sort by RRF score descending
        ranked_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        top_ranked = ranked_docs[:top_n]
        
        # 4. Confidence Gating (Layer 3)
        # Check if the highest score clears the threshold
        top_score = top_ranked[0][1] if top_ranked else 0.0
        is_confident = top_score >= self.confidence_threshold
        
        # Format results
        results = []
        for doc_id, score in top_ranked:
            if doc_id in doc_map:
                res = doc_map[doc_id]
                res["id"] = doc_id
                res["rrf_score"] = score
                results.append(res)
                
        return results, is_confident
