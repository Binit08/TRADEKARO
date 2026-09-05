# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for the TradeKaro NLconverter project.

An ADR is a short text file that captures an important architectural decision made along with its context and consequences.

## Index

* [0001 - Hybrid Retrieval (BM25 + Dense) Over Dense-Only for RAG](./0001-hybrid-retrieval-over-dense-only.md)
* [0002 - SQLite/PostgreSQL Over Parquet for Primary Storage](./0002-sqlite-postgres-over-parquet.md)

## How to add an ADR

1. Copy `template.md` to a new file named `NNNN-short-title.md` (where NNNN is the next sequential number).
2. Fill in the template with the details of the decision.
3. Add a link to the new ADR in the Index above.
4. Submit via Pull Request.
