"""Script to ingest knowledge documents and build a DuckDB vector search index."""

import json
import os
import sys
from pathlib import Path

# Add the backend directory to sys.path so we can import from strategy_parser
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

import duckdb
from strategy_parser.rag.models import KnowledgeDoc
from strategy_parser.rag.embedding import GeminiEmbeddingClient
from strategy_parser.utils import load_dotenv

load_dotenv()

DB_PATH = backend_dir / "data" / "knowledge_base.duckdb"
CORPUS_PATH = backend_dir / "data" / "knowledge_corpus.json"

def main():
    print(f"Loading corpus from {CORPUS_PATH}...")
    if not CORPUS_PATH.exists():
        print(f"Corpus file not found: {CORPUS_PATH}")
        sys.exit(1)

    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate against Pydantic schema
    docs = [KnowledgeDoc(**item) for item in data]
    print(f"Loaded {len(docs)} documents.")

    print("Initializing embedding client...")
    # This will use GOOGLE_GEMINI_API_KEY from environment
    embedding_client = GeminiEmbeddingClient()

    print(f"Connecting to DuckDB at {DB_PATH}...")
    conn = duckdb.connect(str(DB_PATH))

    # Install and load required extensions
    print("Loading VSS and FTS extensions...")
    conn.execute("INSTALL vss;")
    conn.execute("LOAD vss;")
    conn.execute("INSTALL fts;")
    conn.execute("LOAD fts;")

    # Setup the table
    print("Setting up table schema...")
    conn.execute("DROP TABLE IF EXISTS knowledge_docs;")
    
    # We use FLOAT[3072] because Gemini gemini-embedding-001 produces 3072-dimensional vectors
    conn.execute("""
        CREATE TABLE knowledge_docs (
            id VARCHAR PRIMARY KEY,
            type VARCHAR,
            canonical_name VARCHAR,
            aliases VARCHAR[],
            maps_to_field VARCHAR,
            embedding_text TEXT,
            metadata JSON,
            vec FLOAT[3072]
        );
    """)

    print("Generating embeddings and inserting records...")
    for doc in docs:
        try:
            print(f"  Embedding: {doc.id} ({doc.canonical_name})", flush=True)
        except UnicodeEncodeError:
            print(f"  Embedding: {doc.id} (name has unicode chars)", flush=True)
        # Generate dense vector
        vec = embedding_client.embed_text(doc.embedding_text)
        
        # Serialize metadata properly for DuckDB JSON
        meta_str = json.dumps(doc.metadata) if doc.metadata else "{}"
        
        # Insert into database
        conn.execute("""
            INSERT INTO knowledge_docs 
            (id, type, canonical_name, aliases, maps_to_field, embedding_text, metadata, vec) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc.id, 
            doc.type, 
            doc.canonical_name, 
            doc.aliases, 
            doc.maps_to_field, 
            doc.embedding_text, 
            meta_str, 
            vec
        ))

    print("Building Vector Search Index (HNSW)...")
    conn.execute("SET hnsw_enable_experimental_persistence = true;")
    conn.execute("""
        CREATE INDEX doc_vec_idx ON knowledge_docs USING HNSW (vec);
    """)

    # We rely on ILIKE in python for sparse search to avoid extension persistence issues
    print("Index build complete!")
    conn.close()

if __name__ == "__main__":
    main()
