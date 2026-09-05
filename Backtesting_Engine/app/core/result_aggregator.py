from typing import Dict, List, Any
import pandas as pd
from datetime import datetime

from app.execution.trade import Trade
from app.config.settings import StrategySettings
from app.metrics.metrics_engine import MetricsEngine
from app.portfolio.portfolio import Portfolio
from app.reports.trade_report import ReportBuilder


class ResultAggregator:
    """Aggregates backtest results and metrics across multiple portfolios."""
    
    def __init__(self, metrics: MetricsEngine, base_portfolio: Portfolio, portfolios: Dict[str, Portfolio]):
        self.metrics = metrics
        self.base_portfolio = base_portfolio
        self.portfolios = portfolios

    def aggregate(self, settings: StrategySettings, fills: List[Trade]) -> Dict[str, Any]:
        """Process all fills and portfolio states into a final result summary."""
        combined_closed_trades = []
        combined_open_trades = []
        
        df_list = []
        symbol_results = {}
        for sym, port in self.portfolios.items():
            eq = port.equity_curve()
            df = pd.DataFrame(eq)
            if not df.empty and "timestamp" in df.columns:
                df = df.set_index("timestamp")
                df_list.append(df[["equity"]].rename(columns={"equity": sym}))
            
            sym_metrics = self.metrics.compute(
                port.equity_history,
                port.trade_history,
                portfolio_unrealized_pnl=port.get_unrealized_pnl(),
                equity_curve=eq,
            )
            
            closed = [trade for trade in port.trade_history if trade.status == "CLOSED"]
            open_t = [trade for trade in port.trade_history if trade.status == "OPEN"]
            
            symbol_results[sym] = {
                "portfolio": port.summary(),
                "metrics": sym_metrics,
                "trade_report": ReportBuilder.build_trade_report(port),
                "equity_curve": eq,
            }
            combined_closed_trades.extend(closed)
            combined_open_trades.extend(open_t)

        if df_list:
            agg_df = pd.concat(df_list, axis=1).ffill().fillna(self.base_portfolio.initial_cash)
            agg_df["total_equity"] = agg_df.sum(axis=1)
            
            agg_equity_curve = []
            running_max = sum(p.initial_cash for p in self.portfolios.values()) if self.portfolios else 0
            for i, (ts, row) in enumerate(agg_df.iterrows()):
                eq = float(row["total_equity"])
                if eq > running_max:
                    running_max = eq
                dd_pct = ((running_max - eq) / running_max) * 100.0 if running_max > 0 else 0.0
                
                agg_equity_curve.append({
                    "step": i,
                    "timestamp": ts,
                    "equity": eq,
                    "cash": 0.0,
                    "drawdown_pct": dd_pct
                })
        else:
            agg_equity_curve = []
            
        agg_equity_history = [p["equity"] for p in agg_equity_curve]
        all_trade_history = []
        unrealized = 0.0
        for p in self.portfolios.values():
            all_trade_history.extend(p.trade_history)
            unrealized += p.get_unrealized_pnl()
        
        all_trade_history.sort(key=lambda t: t.entry_time or datetime.min)
        
        metrics_summary = self.metrics.compute(
            agg_equity_history,
            all_trade_history,
            portfolio_unrealized_pnl=unrealized,
            equity_curve=agg_equity_curve,
        )
        
        return {
            "portfolio": {"cash": sum(p.cash for p in self.portfolios.values()), "equity": agg_equity_history[-1] if agg_equity_history else 0},
            "metrics": metrics_summary,
            "trades": fills,
            "fills": fills,
            "closed_trades": combined_closed_trades,
            "open_trades": combined_open_trades,
            "equity_curve": agg_equity_curve,
            "trade_report": [r for sym_res in symbol_results.values() for r in sym_res["trade_report"]],
            "settings": settings.to_dict(),
            "warnings": [],  # Will be populated by the caller
            "symbol_results": symbol_results,
        }
