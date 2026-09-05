# AI Algorithmic Trading Platform

Welcome to the comprehensive documentation for the complete trading ecosystem.

This platform is divided into two distinct, highly specialized microservices that work in tandem to democratize algorithmic trading:

1. **[The Natural Language Converter (NLconverter)](nlconverter/overview.md)**: A full-stack application that translates plain English trading ideas into strict, mathematically verifiable JSON structures using Large Language Models (Google Gemini).
2. **[The Backtesting Engine (Core)](backtest/overview.md)**: A blazingly fast, Python-based financial simulator that ingests the JSON output from the NLconverter, processes historical market data, and simulates executions to generate institutional-grade performance metrics.

By strictly decoupling the natural language interpretation (Frontend/LLM) from the mathematical execution (Backend Engine), the platform ensures deterministic, reproducible, and secure backtesting without the security risks of arbitrary code execution.

Please navigate using the sidebar to explore the deep architectural dives into each component.
