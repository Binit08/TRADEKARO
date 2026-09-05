# Natural Language Converter: Current Limitations & Future Roadmap

This document outlines the current limitations of the Natural Language (NL) to AST converter, specifically focusing on the gap between human trading concepts and deterministic software execution. It also provides a roadmap for how these gaps will be bridged in future updates.

## 1. The Core Limitation: Determinism vs. Subjectivity

The converter is currently built to translate natural language into a **strict, deterministic Abstract Syntax Tree (AST)**. This means every instruction must be perfectly quantifiable. 

### What the Software Excels At (Current Capabilities)
The software currently perfectly parses **quantitative instructions**:
- Standard Indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR)
- Strict mathematical conditions (`CROSS_ABOVE`, `LESS_THAN`)
- Concrete values and lookbacks ("50-day EMA", "previous candle close", "Volume > 200k")
- Hard risk parameters ("2% stop loss", "take profit at 3:1 risk/reward")

### What the Software Blocks (Current Limitations)  
The AI is instructed to `block` strategies that contain **qualitative or subjective concepts** because the AST cannot execute "feelings" or visual chart abstractions. 

Currently unsupported concepts include:
- **Abstract Market Structure:** "Liquidity sweeps", "institutional manipulation", "fair value gaps".
- **Subjective Charting:** "Support and resistance levels", "trendlines", "quarterly levels".
- **Ambiguous Price Action:** "Price pulls back *close to* the EMA", "the market is *choppy*", "wait for a *retest*".
- **Vague Risk Rules:** "Avoid *tight* stop losses", "stop loss at the *previous low/high*" (without a specific lookback window).

## 2. Technical Limitations

### Lack of Path-Dependent State Tracking (Memory)
- **Severity:** High
- **Cause:** The ASTBuilder is strictly hierarchical and declarative. There is no concept of variable assignment, `for`/`while` loops, or complex state memory (e.g., "Remember the price when MACD crossed yesterday and buy if it touches that price again").
- **Impact:** While it supports `SEQUENCE` nodes, it cannot handle strategies that require dynamic variables or custom order blocks (like the exact one we had to write a custom Pandas script for earlier).

---

## 3. Future Implementation Roadmap

To bridge the gap between human intuition and machine determinism, the following features are planned for future implementation:

### A. The "Heuristics" Engine (Translating Concepts to Math)
We will introduce a middle-layer that maps abstract concepts to strict mathematical heuristics. 
* **Support/Resistance:** Automatically translated to `N-period Rolling High/Low` or `Pivot Points`.
* **Liquidity Sweeps:** Translated to `Price drops below N-period Low AND closes back above it within M periods`.
* **Consolidation/Choppiness:** Translated to `Bollinger Band Width < X` or `ADX < 20`.

### B. Interactive LLM Clarification Flow
Instead of just blocking a strategy, the AI will enter an interactive flow to clarify ambiguity with the user:
* *User:* "Avoid tight stop losses."
* *AI:* "I cannot compile 'tight stop losses'. Would you like me to set the stop loss to `2 * ATR` to account for volatility?"

### C. Advanced Pattern Recognition Schema
The schema will be expanded to natively support structural chart patterns.
* Introducing new `pattern_type` primitives: `DOUBLE_TOP`, `HEAD_AND_SHOULDERS`, `BULL_FLAG`.
* The AST will hook into a specialized pattern recognition microservice rather than trying to build these patterns via standard indicator math.

### D. Multi-Timeframe (MTF) Context Awareness
Currently, instructing the AI to "Check the weekly trend and buy on the 15-minute chart" requires complex AST scaffolding. The schema will be updated to allow assigning `resolution` overrides on a per-indicator basis natively, making MTF strategies much easier to parse.

---

> [!NOTE]
> **Summary**
> The AI is currently doing exactly what it was designed to do: rejecting strategies that a machine cannot mathematically execute. The future of the software is not about making the AST less strict, but about making the AI smarter at translating human concepts into strict math.
