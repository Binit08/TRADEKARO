import React from 'react';
import Gauge from '../charts/Gauge';

interface Metrics {
  net_pnl: number;
  return_pct: number;
  win_rate: number;
  max_drawdown: number;
  profit_factor: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  sharpe_ratio?: number;
  sortino_ratio?: number;
  max_drawdown_duration?: string | number;
}

export default function OverviewCards({ metrics }: { metrics: Metrics }) {
  if (!metrics) return null;
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {/* Primary Metrics (Gauges) */}
      <div className="metric-card col-span-2 lg:col-span-1 row-span-2 flex flex-col items-center justify-center bg-background">
        <div className="text-[11px] font-bold text-muted uppercase tracking-widest absolute top-4 left-4 font-industrial">Win Rate</div>
        <div className="mt-6 w-full">
          {metrics.win_rate != null ? (
            <Gauge value={metrics.win_rate} min={0} max={100} unit="%" color="#10B981" />
          ) : (
            <span className="text-muted font-medium flex justify-center mt-10">N/A</span>
          )}
        </div>
      </div>

      <div className="metric-card col-span-2 lg:col-span-1 row-span-2 flex flex-col items-center justify-center bg-background">
        <div className="text-[11px] font-bold text-muted uppercase tracking-widest absolute top-4 left-4 font-industrial">Profit Factor</div>
        <div className="mt-6 w-full">
          {metrics.profit_factor != null && metrics.profit_factor !== Infinity ? (
            <Gauge value={metrics.profit_factor} min={0} max={3} color="#3B82F6" />
          ) : (
            <span className="text-muted font-medium flex justify-center mt-10">N/A</span>
          )}
        </div>
      </div>

      {/* Standard Metric Cards */}
      <div className="metric-card">
        <div className="text-[10px] font-bold text-muted uppercase tracking-widest font-industrial">Net Profit</div>
        <div className={`text-2xl font-industrial font-bold mt-2 ${(metrics.net_pnl ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
          {(metrics.net_pnl ?? 0) >= 0 ? '+' : ''}
          {(metrics.net_pnl ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
      </div>

      <div className="metric-card">
        <div className="text-[10px] font-bold text-muted uppercase tracking-widest font-industrial">Return %</div>
        <div className={`text-2xl font-industrial font-bold mt-2 ${(metrics.return_pct ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
          {(metrics.return_pct ?? 0) >= 0 ? '+' : ''}
          {(metrics.return_pct ?? 0).toFixed(2)}%
        </div>
      </div>

      <div className="metric-card">
        <div className="text-[10px] font-bold text-muted uppercase tracking-widest font-industrial">Total Trades</div>
        <div className="text-2xl font-industrial font-bold text-foreground mt-2">
          {metrics.total_trades ?? 0}
        </div>
        <div className="text-[10px] mt-1 text-muted font-industrial">
          <span className="text-emerald-600">{metrics.winning_trades ?? 0} W</span> / <span className="text-rose-600">{metrics.losing_trades ?? 0} L</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="text-[10px] font-bold text-muted uppercase tracking-widest font-industrial">Max Drawdown</div>
        <div className="text-2xl font-industrial font-bold text-rose-600 mt-2">
          {metrics.max_drawdown != null ? `-${Math.abs(metrics.max_drawdown).toFixed(2)}%` : <span className="text-muted font-medium text-lg">N/A</span>}
        </div>
      </div>

      <div className="metric-card">
        <div className="text-[10px] font-bold text-muted uppercase tracking-widest font-industrial">Sharpe Ratio</div>
        <div className="text-2xl font-industrial font-bold text-foreground mt-2">
          {metrics.sharpe_ratio != null ? metrics.sharpe_ratio.toFixed(2) : <span className="text-muted font-medium text-lg">N/A</span>}
        </div>
      </div>

      <div className="metric-card">
        <div className="text-[10px] font-bold text-muted uppercase tracking-widest font-industrial">Sortino Ratio</div>
        <div className="text-2xl font-industrial font-bold text-foreground mt-2">
          {metrics.sortino_ratio != null ? metrics.sortino_ratio.toFixed(2) : <span className="text-muted font-medium text-lg">N/A</span>}
        </div>
      </div>

    </div>
  );
}

