# 0001 - Hybrid Retrieval (BM25 + Dense) Over Dense-Only for RAG

* **Status:** Accepted
* **Date:** 2026-09-02
* **Authors:** TradeKaro Team

## Context

The Semantic Resolver stage of the NLconverter pipeline requires an entity disambiguation system (RAG) to map ambiguous user terminology (e.g., "moving avg") to canonical schema indicators (e.g., "SMA"). 

Initially, a dense-only vector search using embeddings (`sentence-transformers`) was considered. However, trading jargon often involves exact acronyms ("RSI", "MACD") or specific numbers ("200-day"). Dense embeddings are excellent at semantic similarity but frequently fail at exact keyword matching (e.g., distinguishing "RSI" from "MFI" if they appear in similar contexts, or matching exact ticker symbols).

## Decision

We will use a **Hybrid Retrieval** approach combining Dense Search (Vector Similarity Search) and Sparse Search (Full-Text Search / BM25) over a dense-only approach.

We implemented this using DuckDB with the `vss` and `fts` extensions. The results from both searches are merged and re-ranked using **Reciprocal Rank Fusion (RRF)** with a constant `k=60`.

*Note: Due to DuckDB FTS persistence issues in the current version, the sparse search is temporarily implemented using `ILIKE` keyword matching, but the architectural fusion remains the same.*

## Consequences

### Positive

* **Higher Accuracy:** Exact acronyms (MACD, VWAP) are matched perfectly by the sparse search, while descriptive concepts ("trend following line") are matched by the dense search.
* **Resilience to Typos:** Dense embeddings handle misspelled terms well, ensuring robust parsing of user input.

### Negative

* **Performance Overhead:** Running two separate queries and fusing them in Python adds slight latency compared to a single dense query.
* **Storage Footprint:** Requires storing both the text index (or text strings) and the 384-dimensional vector embeddings in the DuckDB file.
