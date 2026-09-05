"""Paper Trading Orchestration.

Reuses the event-driven Phase 2 pipeline from BacktestEngine but replaces
the historical data loader with the LiveKiteFeed and ExecutionEngine with PaperExecutionEngine.
"""
from __future__ import annotations

import logging
import threading
import concurrent.futures
from typing import Any, Dict, List, Optional, Union

from app.core.backtest_engine import BacktestEngine
from app.config.settings import StrategySettings
from app.execution.trade import Trade
from app.ast.validator import validate as validate_ast
from app.ast.indicator_extractor import IndicatorExtractor
from app.core.order_manager import OrderManager
from app.portfolio.portfolio import Portfolio
from app.indicators.indicator_engine import IndicatorEngine

logger = logging.getLogger(__name__)


class PaperTradingEngine(BacktestEngine):
    """Orchestrates paper trading for a strategy."""

    def _prepare_paper_run(
        self,
        symbols: List[str],
        strategy_ast: Dict[str, Any],
        strategy_settings: Union[StrategySettings, Dict[str, Any], None],
    ):
        """Prepare the engine for a live paper trading session.
        
        Differs from BacktestEngine._prepare_run because it does NOT 
        load historical CSV data. It relies on the pre-injected LiveKiteFeed.
        """
        self._run_warnings.clear()
        
        execution_ctx = strategy_ast.get("execution_context") if isinstance(strategy_ast, dict) else None
        settings = self._resolve_settings(strategy_settings, execution_ctx, strategy_ast=strategy_ast if isinstance(strategy_ast, dict) else None)
        self._configure_execution(settings)

        # Reset components
        self.feed.reset()
        self.indicator.reset()
        self.signal.reset()
        self.execution.reset()
        
        self.portfolios = {sym: Portfolio(initial_cash=self.portfolio.initial_cash, short_margin_pct=settings.short_margin_pct) for sym in symbols}
        self.metrics.reset()
        
        self.order_manager = OrderManager(self.execution, self.portfolios, self._run_warnings)

        validate_ast(strategy_ast)
        indicator_configs = IndicatorExtractor.gather_indicator_configs(strategy_ast, self.indicator_configs)
        IndicatorExtractor.validate_indicator_configs(indicator_configs, self.indicator.available())

        self.indicators = {sym: IndicatorEngine() for sym in symbols}

        return settings, indicator_configs, self.feed

    def run_paper(
        self,
        symbols: List[str],
        strategy_ast: Dict[str, Any],
        strategy_settings: Union[StrategySettings, Dict[str, Any], None] = None,
        cancel_event: Optional[threading.Event] = None,
        on_update: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """Run a continuous paper trading session."""
        if cancel_event is None:
            cancel_event = threading.Event()

        def _run_implementation():
            # Phase 1: Setup
            settings, indicator_configs, feed = self._prepare_paper_run(
                symbols, strategy_ast, strategy_settings
            )

            fills: List[Trade] = []
            symbol_indices = {sym: 0 for sym in symbols}

            logger.info(f"Started Paper Trading session for {symbols}")

            # Phase 2: Live Execution Pipeline
            # Note: feed.stream() is a blocking generator yielding live candles
            for _, candle in enumerate(feed.stream()):
                if cancel_event is not None and cancel_event.is_set():
                    logger.info("Paper trading session cancelled.")
                    break
                
                # Step 2a: Execute pending orders
                self._execute_pending_orders(candle, settings, fills)
                
                # Step 2b: Process protective stops
                self._process_protective_stops(candle, settings, fills)
                
                # Step 2c: Update indicators
                indicators = self._update_indicators(candle, symbol_indices)
                
                # Step 2d: Generate signals and submit new orders
                self._generate_and_submit_orders(candle, settings, strategy_ast, indicators)
                
                # Step 2e: Update portfolio MTM
                self._update_portfolio_mtm(candle)
                
                # Step 2f: Notify listeners (e.g. WebSocket)
                if on_update:
                    try:
                        on_update(candle, indicators, self.execution.trade_history.copy(), self.portfolios)
                    except Exception as e:
                        logger.error(f"Error in on_update callback: {e}")

            # Phase 3: Aggregation when session stopped
            from app.core.result_aggregator import ResultAggregator
            aggregator = ResultAggregator(self.metrics, self.portfolio, self.portfolios)
            res = aggregator.aggregate(settings, fills)
            res["warnings"] = list(getattr(self.signal, "warnings", [])) + res.get("metrics", {}).get("warnings", []) + self._run_warnings
            return res

        # Paper trading runs until cancelled, so we don't strictly timeout
        # but we use a ThreadPool to keep it isolated.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_implementation)
            try:
                # Wait indefinitely until cancelled or error
                return future.result()
            except Exception as e:
                logger.error(f"Paper trading crashed: {e}")
                cancel_event.set()
                raise e
