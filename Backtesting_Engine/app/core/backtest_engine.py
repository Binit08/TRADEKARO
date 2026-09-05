"""End-to-end historical backtest orchestration."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, Union
import logging
import threading
import pandas as pd

from app.ast.validator import validate as validate_ast
from app.config.settings import StrategySettings
from app.core.interfaces import FeedProtocol
from app.data.loader import MarketDataLoader
from app.execution.simulator import ExecutionEngine
from app.execution.trade import Trade
from app.data.market_event import MarketEvent
from app.indicators.indicator_engine import IndicatorEngine
from app.metrics.metrics_engine import MetricsEngine
from app.portfolio.portfolio import Portfolio
from app.signal.signal_engine import SignalEngine
from app.signal.models import SignalType

from app.ast.indicator_extractor import IndicatorExtractor
from app.core.order_manager import OrderManager
from app.reports.trade_report import ReportBuilder


class BacktestEngine:
    """Orchestrates a single-symbol historical backtest."""

    def __init__(
        self,
        loader: MarketDataLoader,
        feed: Union[Type[FeedProtocol], FeedProtocol],
        indicator: IndicatorEngine,
        signal: SignalEngine,
        execution: ExecutionEngine,
        portfolio: Portfolio,
        metrics: MetricsEngine,
        indicator_configs: Optional[List[Dict[str, Any]]] = None,
        settings: Union[StrategySettings, Dict[str, Any], None] = None,
    ) -> None:
        self.loader = loader
        self.feed = feed
        self.indicator = indicator
        self.signal = signal
        self.execution = execution
        self.portfolio = portfolio
        self.metrics = metrics
        self.indicator_configs = indicator_configs or []
        self.settings = StrategySettings.from_any(settings)
        self._run_warnings: List[str] = []
        self.timeout_seconds: float = 60.0
        
        self.order_manager: Optional[OrderManager] = None

    def run(
        self,
        symbols: Union[str, List[str]],
        start: str,
        end: str,
        timeframe: str,
        strategy_ast: Dict[str, Any],
        strategy_settings: Union[StrategySettings, Dict[str, Any], None] = None,
        cancel_event: Optional[threading.Event] = None,
        broker: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run a backtest for a single symbol and return summary results."""
        # Accept a bare string for backward compatibility
        if isinstance(symbols, str):
            symbols = [symbols]
        if cancel_event is None:
            cancel_event = threading.Event()

        def _run_implementation():
            # Phase 1: Setup and Initialization
            settings, events, indicator_configs, feed = self._prepare_run(
                symbols, start, end, timeframe, strategy_ast, strategy_settings, broker
            )

            fills: List[Trade] = []
            symbol_indices = {sym: 0 for sym in symbols}

            import pandas as pd
            start_ts = pd.to_datetime(start, utc=True)
            
            # Phase 2: Execution Pipeline
            for _, candle in enumerate(feed.stream()):
                if cancel_event is not None and cancel_event.is_set():
                    raise TimeoutError("Backtest execution cancelled/timed out")
                
                # Step 2c: Update indicators MUST run for every candle to keep snapshot index synced
                indicators = self._update_indicators(candle, symbol_indices)
                
                # Step 2a: Execute pending orders
                exit_fills_on_this_bar = self._execute_pending_orders(candle, settings, fills)
                
                # Step 2b: Process protective stops
                self._process_protective_stops(candle, settings, fills)
                
                # Step 2d: Generate signals and submit new orders
                self._generate_and_submit_orders(candle, settings, strategy_ast, indicators)
                
                # Step 2d-extra: re-entry on exit bar (TradingView-compatible mode)
                # If a position was just closed by an EXIT fill this bar, and the entry
                # condition fires on this bar's indicators, submit a new entry immediately.
                if settings.reentry_on_exit_bar and exit_fills_on_this_bar:
                    for fill in exit_fills_on_this_bar:
                        if getattr(fill, "intent", "") == "EXIT":
                            self._generate_and_submit_orders(candle, settings, strategy_ast, indicators)
                            break  # one re-evaluation per bar is sufficient
                            
                # Step 2e: Execute same-candle market orders if execution_mode is same_candle_close
                if getattr(settings, "execution_mode", "next_candle_open") == "same_candle_close":
                    same_candle_fills = self.execution.execute_market_orders_at_close(candle)
                    for fill in same_candle_fills:
                        protective_fill = self.order_manager.process_fill(fill, settings, candle)
                        fills.append(fill)
                        if protective_fill is not None:
                            fills.append(protective_fill)
                
                # Step 2e: Update portfolio MTM
                self._update_portfolio_mtm(candle)

            # Phase 3: Aggregation and Reporting
            from app.core.result_aggregator import ResultAggregator
            aggregator = ResultAggregator(self.metrics, self.portfolio, self.portfolios)
            res = aggregator.aggregate(settings, fills)
            res["warnings"] = list(getattr(self.signal, "warnings", [])) + res.get("metrics", {}).get("warnings", []) + self._run_warnings
            return res

        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_implementation)
            try:
                return future.result(timeout=self.timeout_seconds)
            except concurrent.futures.TimeoutError:
                cancel_event.set()
                raise TimeoutError(f"Backtest execution timed out after {self.timeout_seconds} seconds")

    def _prepare_run(
        self,
        symbols: List[str],
        start: str,
        end: str,
        timeframe: str,
        strategy_ast: Dict[str, Any],
        strategy_settings: Union[StrategySettings, Dict[str, Any], None],
        broker: Optional[Dict[str, Any]] = None,
    ):
        self._run_warnings.clear()
        if not hasattr(self.indicator, "compute_all") or not hasattr(self.indicator, "get_snapshot"):
            raise AttributeError("Custom indicator engine must implement 'compute_all' and 'get_snapshot'.")

        execution_ctx = strategy_ast.get("execution_context") if isinstance(strategy_ast, dict) else None
        settings = self._resolve_settings(strategy_settings, execution_ctx, strategy_ast=strategy_ast if isinstance(strategy_ast, dict) else None)
        self._configure_execution(settings)

        validate_ast(strategy_ast)
        indicator_configs = IndicatorExtractor.gather_indicator_configs(strategy_ast, self.indicator_configs)
        IndicatorExtractor.validate_indicator_configs(indicator_configs, self.indicator.available())
        
        max_lookback = IndicatorExtractor.get_max_lookback(indicator_configs)

        # loader.load might not support warmup_bars if it's a custom loader, so we handle it gracefully
        load_kwargs = {
            "market_type": settings.market_type,
            "expiry": settings.expiry
        }
        import inspect
        if "warmup_bars" in inspect.signature(self.loader.load).parameters:
            load_kwargs["warmup_bars"] = 0
            
        if "broker" in inspect.signature(self.loader.load).parameters:
            load_kwargs["broker"] = broker

        events = self.loader.load(symbols, start, end, timeframe, **load_kwargs)
        
        if isinstance(self.feed, type):
            feed = self.feed(events)
        else:
            feed = type(self.feed)(events)

        feed.reset()
        self.indicator.reset()
        self.signal.reset()
        self.execution.reset()
        self.portfolios = {sym: Portfolio(initial_cash=self.portfolio.initial_cash, short_margin_pct=settings.short_margin_pct) for sym in symbols}
        self.metrics.reset()
        
        self.order_manager = OrderManager(self.execution, self.portfolios, self._run_warnings)

        self.indicators = {sym: IndicatorEngine() for sym in symbols}
        dfs = self.loader.get_data() if hasattr(self.loader, "get_data") else {}
        
        for sym in symbols:
            df = dfs.get(sym, pd.DataFrame())
            if (df is None or df.empty) and events:
                sym_events = [e for e in events if e.symbol == sym]
                df = pd.DataFrame([{
                    "timestamp": getattr(e, "timestamp", None),
                    "open": float(e.open),
                    "high": float(e.high),
                    "low": float(e.low),
                    "close": float(e.close),
                    "volume": float(getattr(e, "volume", 0.0) or 0.0),
                } for e in sym_events])
            self.indicators[sym].compute_all(df, indicator_configs)
            
        return settings, events, indicator_configs, feed

    def _execute_pending_orders(self, candle, settings, fills):
        exit_fills = []
        for fill in self.execution.execute_all(candle):
            if getattr(fill, "order_created_time", None) is not None:
                intent = str(getattr(fill, "intent", "ENTRY")).upper()
                reason = str(getattr(fill, "entry_reason", "")).upper()
                order_created_time = fill.order_created_time
                if intent == "ENTRY":
                    assert candle.timestamp > order_created_time, (
                        f"Lookahead violation: Entry order created at {order_created_time} "
                        f"filled at {candle.timestamp} on the same/earlier candle."
                    )
                elif intent == "EXIT" and reason in ("STOP_LOSS", "TAKE_PROFIT"):
                    assert candle.timestamp >= order_created_time, (
                        f"Lookahead violation: Protective exit order created at {order_created_time} "
                        f"filled at {candle.timestamp} before creation time."
                    )
            try:
                protective_fill = self.order_manager.process_fill(fill, settings, candle)
                fills.append(fill)
                if getattr(fill, "intent", "") == "EXIT":
                    exit_fills.append(fill)
                if protective_fill is not None:
                    fills.append(protective_fill)
            except ValueError as e:
                logging.getLogger(__name__).error(
                    "Execution fill rejected: symbol=%s side=%s price=%s qty=%s reason=%s error=%s",
                    fill.symbol, fill.side, fill.entry_price, fill.qty, fill.entry_reason, str(e)
                )
        return exit_fills

    def _process_protective_stops(self, candle, settings, fills):
        try:
            protective_fill = self.order_manager.process_protective_exit(candle, settings)
            if protective_fill is not None:
                fills.append(protective_fill)
        except ValueError as e:
            logging.getLogger(__name__).error(
                "Protective exit fill rejected: symbol=%s error=%s",
                candle.symbol, str(e)
            )

    def _update_indicators(self, candle, symbol_indices):
        sym = candle.symbol
        idx = symbol_indices.get(sym, 0)
        indicators = self.indicators[sym].get_snapshot(idx)
        symbol_indices[sym] = idx + 1
        return indicators

    def _generate_and_submit_orders(self, candle, settings, strategy_ast, indicators):
        market_data = {
            "CLOSE": float(candle.close),
            "HIGH": float(candle.high),
            "LOW": float(candle.low),
            "OPEN": float(candle.open),
            "VOLUME": float(getattr(candle, "volume", 0.0) or 0.0),
        }
        
        position = self.portfolios[candle.symbol].positions.get(candle.symbol) if candle.symbol in self.portfolios else None
        current_position_side = position.side if position else None
        
        if position and current_position_side != "FLAT":
            market_data["ENTRY_PRICE"] = float(position.entry_price)
            market_data["POSITION_QTY"] = float(position.qty)
            market_data["UNREALIZED_PNL"] = float(position.unrealized_pnl)
            if position.entry_price > 0:
                if current_position_side == "SHORT":
                    pnl_pct = ((position.entry_price - candle.close) / position.entry_price) * 100.0
                else:
                    pnl_pct = ((candle.close - position.entry_price) / position.entry_price) * 100.0
                market_data["UNREALIZED_PNL_PERCENT"] = float(pnl_pct)
        
        try:
            signal = self.signal.evaluate(
                strategy_ast,
                indicators,
                default=settings.default_signal,
                market_data=market_data,
                current_position_side=current_position_side,
            )
        except TypeError:
            try:
                signal = self.signal.evaluate(
                    strategy_ast,
                    indicators,
                    default=settings.default_signal,
                    current_position_side=current_position_side,
                )
            except TypeError:
                signal = self.signal.evaluate(
                    strategy_ast,
                    indicators,
                    default=settings.default_signal,
                )
        self.order_manager.submit_signal_order(signal, candle, settings)

    def _update_portfolio_mtm(self, candle):
        if candle.symbol in self.portfolios:
            self.portfolios[candle.symbol].mark_to_market(candle)

    def _resolve_settings(
        self,
        runtime_settings: Union[StrategySettings, Dict[str, Any], None],
        execution_ctx: Optional[Dict[str, Any]] = None,
        strategy_ast: Optional[Dict[str, Any]] = None,
    ) -> StrategySettings:
        base = self.settings
        if isinstance(execution_ctx, dict) and execution_ctx:
            try:
                base = StrategySettings.from_execution_context(execution_ctx, base)
            except Exception as exc:
                logging.getLogger(__name__).warning("Could not apply execution_context: %s", exc)
        if isinstance(strategy_ast, dict):
            try:
                base = StrategySettings.from_ast_risk_node(strategy_ast, base)
            except Exception as exc:
                logging.getLogger(__name__).warning("Could not apply AST risk_node: %s", exc)
        if runtime_settings is None:
            return base
        base_dict = base.to_dict()
        if isinstance(runtime_settings, dict):
            valid_keys = set(StrategySettings.__dataclass_fields__)
            overrides = {}
            for k, v in runtime_settings.items():
                if k in valid_keys:
                    overrides[k] = v
                else:
                    logging.getLogger(__name__).warning("Filtered out unsupported settings key: '%s'", k)
        else:
            overrides = StrategySettings.from_any(runtime_settings).to_dict()
        for key, value in overrides.items():
            if value is not None:
                base_dict[key] = value
        return StrategySettings.from_any(base_dict)

    def _configure_execution(self, settings: StrategySettings) -> None:
        self.execution.configure_costs(
            fee_rate=settings.commission_rate,
            fixed_fee=settings.fixed_commission,
            min_fee=settings.min_commission,
            slippage_bps=settings.slippage_bps,
            multiplier=settings.multiplier,
            margin=settings.margin,
        )
