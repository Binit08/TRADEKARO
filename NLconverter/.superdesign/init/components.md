# Components

## frontend/src/components/metrics/OverviewCards.tsx
```tsx
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
      <div className="metric-card col-span-2 lg:col-span-1 row-span-2 flex flex-col items-center justify-center bg-slate-50">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-widest absolute top-4 left-4 font-industrial">Win Rate</div>
        <div className="mt-6 w-full">
          {metrics.win_rate != null ? (
            <Gauge value={metrics.win_rate} min={0} max={100} title="Win Rate" unit="%" color="#10B981" />
          ) : (
            <span className="text-slate-400 font-medium flex justify-center mt-10">N/A</span>
          )}
        </div>
      </div>

      <div className="metric-card col-span-2 lg:col-span-1 row-span-2 flex flex-col items-center justify-center bg-slate-50">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-widest absolute top-4 left-4 font-industrial">Profit Factor</div>
        <div className="mt-6 w-full">
          {metrics.profit_factor != null && metrics.profit_factor !== Infinity ? (
            <Gauge value={metrics.profit_factor} min={0} max={3} title="Profit Factor" color="#3B82F6" />
          ) : (
            <span className="text-slate-400 font-medium flex justify-center mt-10">N/A</span>
          )}
        </div>
      </div>

      {/* Standard Metric Cards */}
      <div className="metric-card">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest font-industrial">Net Profit</div>
        <div className={`text-2xl font-industrial font-bold mt-2 ${metrics.net_pnl >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
          {metrics.net_pnl >= 0 ? '+' : ''}
          {metrics.net_pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
      </div>

      <div className="metric-card">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest font-industrial">Return %</div>
        <div className={`text-2xl font-industrial font-bold mt-2 ${metrics.return_pct >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
          {metrics.return_pct >= 0 ? '+' : ''}
          {metrics.return_pct.toFixed(2)}%
        </div>
      </div>

      <div className="metric-card">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest font-industrial">Total Trades</div>
        <div className="text-2xl font-industrial font-bold text-slate-900 mt-2">
          {metrics.total_trades}
        </div>
        <div className="text-[10px] mt-1 text-slate-500 font-industrial">
          <span className="text-emerald-600">{metrics.winning_trades} W</span> / <span className="text-rose-600">{metrics.losing_trades} L</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest font-industrial">Max Drawdown</div>
        <div className="text-2xl font-industrial font-bold text-rose-600 mt-2">
          {metrics.max_drawdown != null ? `-${Math.abs(metrics.max_drawdown).toFixed(2)}%` : <span className="text-slate-400 font-medium text-lg">N/A</span>}
        </div>
      </div>

      <div className="metric-card">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest font-industrial">Sharpe Ratio</div>
        <div className="text-2xl font-industrial font-bold text-slate-900 mt-2">
          {metrics.sharpe_ratio != null ? metrics.sharpe_ratio.toFixed(2) : <span className="text-slate-400 font-medium text-lg">N/A</span>}
        </div>
      </div>

      <div className="metric-card">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest font-industrial">Sortino Ratio</div>
        <div className="text-2xl font-industrial font-bold text-slate-900 mt-2">
          {metrics.sortino_ratio != null ? metrics.sortino_ratio.toFixed(2) : <span className="text-slate-400 font-medium text-lg">N/A</span>}
        </div>
      </div>

    </div>
  );
}


```

## frontend/src/components/trades/TradeListTable.tsx
```tsx
import React, { useState } from 'react';

interface Trade {
  entry_time: string;
  exit_time?: string;
  symbol: string;
  side: string;
  qty: number;
  entry_price: number;
  exit_price?: number;
  pnl?: number;
  return_pct?: number;
  unrealized_pnl?: number;
  current_price?: number;
}

interface TradeListTableProps {
  trades: Trade[];
}

export default function TradeListTable({ trades }: TradeListTableProps) {
  const [filterSide, setFilterSide] = useState('ALL');

  const normalizeSide = (s: string) => {
    const upper = s?.toUpperCase() || '';
    if (upper === 'BUY' || upper === 'LONG') return 'LONG';
    if (upper === 'SELL' || upper === 'SHORT') return 'SHORT';
    return upper;
  };

  const filteredTrades = trades.filter((t) => filterSide === 'ALL' || normalizeSide(t.side) === filterSide);

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden flex flex-col h-full">
      <div className="px-5 py-3 border-b border-slate-200 flex items-center justify-between bg-slate-100">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-yellow-500 animate-pulse"></div>
          <h4 className="text-[11px] font-bold text-slate-800 uppercase tracking-widest font-industrial">Execution Log</h4>
        </div>
        <div className="flex gap-3">
          <select 
            value={filterSide} 
            onChange={(e) => setFilterSide(e.target.value)}
            className="text-[10px] font-bold uppercase tracking-wider border border-slate-300 rounded px-2 py-1 bg-white text-slate-700 outline-none focus:ring-1 focus:ring-yellow-400 font-industrial"
          >
            <option value="ALL">ALL TYPES</option>
            <option value="LONG">LONG</option>
            <option value="SHORT">SHORT</option>
          </select>
          <span className="text-[10px] font-bold text-slate-700 bg-white border border-slate-200 px-3 py-1 rounded shadow-sm font-industrial flex items-center">
            {filteredTrades.length} TRADES
          </span>
        </div>
      </div>
      
      <div className="overflow-auto flex-1 bg-slate-50">
        {filteredTrades.length === 0 ? (
          <div className="p-8 text-center text-[11px] text-slate-400 font-industrial uppercase tracking-widest">
            No trades match filters
          </div>
        ) : (
          <table className="w-full text-left text-xs border-collapse relative">
            <thead className="sticky top-0 z-10 bg-slate-100/90 backdrop-blur border-b border-slate-200">
              <tr className="text-[10px] font-bold text-slate-500 uppercase tracking-widest font-industrial">
                <th className="py-2.5 px-4 font-semibold">Time</th>
                <th className="py-2.5 px-4 font-semibold">Symbol</th>
                <th className="py-2.5 px-4 font-semibold">Side</th>
                <th className="py-2.5 px-4 font-semibold">Qty</th>
                <th className="py-2.5 px-4 font-semibold">Entry</th>
                <th className="py-2.5 px-4 font-semibold">Exit</th>
                <th className="py-2.5 px-4 text-right font-semibold">PnL</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200/60 font-medium text-slate-700">
              {filteredTrades.map((trade, idx) => {
                const isOpen = trade.exit_price == null;
                const displayPnl = trade.pnl != null ? trade.pnl : trade.unrealized_pnl;
                
                return (
                  <tr key={idx} className="hover:bg-slate-200/50 transition-colors group">
                    <td className="py-2 px-4 font-industrial text-[10px] text-slate-500 whitespace-nowrap">
                      {trade.entry_time.split(' ')[0]} <span className="text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity">{trade.entry_time.split(' ')[1] || ''}</span>
                    </td>
                    <td className="py-2 px-4 font-bold text-slate-900 font-industrial">
                      {trade.symbol}
                    </td>
                    <td className="py-2 px-4">
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded-sm text-[9px] font-black tracking-widest font-industrial ${
                        normalizeSide(trade.side) === 'LONG'
                          ? 'bg-teal-50 text-teal-700 border border-teal-200'
                          : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}>
                        {normalizeSide(trade.side)}
                      </span>
                    </td>
                    <td className="py-2 px-4 font-industrial text-slate-700 text-[11px]">
                      {trade.qty.toFixed(2)}
                    </td>
                    <td className="py-2 px-4 font-industrial text-slate-700 text-[11px]">
                      {trade.entry_price.toFixed(2)}
                    </td>
                    <td className="py-2 px-4 font-industrial text-slate-700 text-[11px]">
                      {!isOpen ? trade.exit_price!.toFixed(2) : (
                        <div className="flex items-center gap-1.5">
                          <span>{trade.current_price != null ? trade.current_price.toFixed(2) : '-'}</span>
                          <span className="text-[8px] font-bold uppercase tracking-widest bg-yellow-100 text-yellow-800 px-1 py-0.5 rounded-sm border border-yellow-200">M2M</span>
                        </div>
                      )}
                    </td>
                    <td className={`py-2 px-4 text-right font-industrial font-black text-[11px] flex justify-end items-center gap-2 ${
                      displayPnl == null
                        ? 'text-slate-400'
                        : displayPnl >= 0
                        ? 'text-emerald-600'
                        : 'text-rose-600'
                    }`}>
                      {isOpen && <span className="text-[9px] font-semibold text-slate-400 uppercase tracking-widest">(Open)</span>}
                      <span>
                        {displayPnl == null ? '-' : `${displayPnl >= 0 ? '+' : ''}${displayPnl.toFixed(2)}`}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}


```

## frontend/src/components/charts/EquityCurveChart.tsx
```tsx
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface EquityCurveChartProps {
  data: { time: string; value: number; benchmark?: number }[];
}

export default function EquityCurveChart({ data }: EquityCurveChartProps) {
  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 20, right: 40, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
          <XAxis 
            dataKey="time" 
            tick={{ fontSize: 10, fill: '#64748b' }} 
            axisLine={false} 
            tickLine={false} 
          />
          <YAxis 
            tick={{ fontSize: 10, fill: '#64748b' }} 
            axisLine={false} 
            tickLine={false} 
            tickFormatter={(val) => val.toLocaleString()}
            domain={['auto', 'auto']}
          />
          <Tooltip 
            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            labelStyle={{ fontWeight: 'bold', color: '#0f172a' }}
            formatter={(value: any) => [value?.toLocaleString() || '', 'Equity']}
          />
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke="#2563eb" 
            strokeWidth={2} 
            dot={false}
            activeDot={{ r: 6, fill: '#2563eb' }}
          />
          <Line 
            type="monotone" 
            dataKey="benchmark" 
            stroke="#94a3b8" 
            strokeWidth={2} 
            dot={false}
            strokeDasharray="5 5"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

```

## frontend/src/components/charts/CandlestickChart.tsx
```tsx
"use client";
import React, { useEffect, useRef } from 'react';
import { createChart, ColorType, ISeriesApi, CandlestickSeries, createSeriesMarkers } from 'lightweight-charts';

interface OHLCCandle {
  time: string | number;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface Trade {
  entry_time: string;
  exit_time?: string;
  side: string;
  qty: number;
  entry_price: number;
  exit_price?: number;
  pnl?: number;
}

interface CandlestickChartProps {
  ohlcData: OHLCCandle[];
  trades: Trade[];
  timeframe: string;
}

export default function CandlestickChart({ ohlcData, trades, timeframe }: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartContainerRef.current || ohlcData.length === 0) return;

    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    // Determine if timeframe is intraday
    const sampleTime = ohlcData[0]?.time;
    const isIntraday = !isNaN(Number(sampleTime)) || (typeof sampleTime === 'string' && !sampleTime.includes('-'));

    // Format OHLC data
    const formattedData = ohlcData.map((d) => {
      const isNum = !isNaN(Number(d.time));
      return {
        time: isNum ? Number(d.time) : d.time,
        open: Number(d.open),
        high: Number(d.high),
        low: Number(d.low),
        close: Number(d.close),
      };
    });

    // Sort OHLC data by time in ascending order to prevent lightweight-charts sorting errors
    formattedData.sort((a, b) => {
      if (typeof a.time === 'number' && typeof b.time === 'number') {
        return a.time - b.time;
      }
      return new Date(a.time as string).getTime() - new Date(b.time as string).getTime();
    });

    // Helper to format trade entry/exit times to align with candle times
    const formatTime = (timeStr: string, isIntradayVal: boolean) => {
      if (!timeStr) return null;
      try {
        if (isIntradayVal) {
          // Parse string format (e.g. "2024-01-05 09:30:00") to epoch seconds
          // Standardize date separator for Safari compliance
          const formattedStr = timeStr.replace(' ', 'T');
          const date = new Date(formattedStr);
          return Math.floor(date.getTime() / 1000);
        } else {
          // Return YYYY-MM-DD format
          return timeStr.split(' ')[0];
        }
      } catch (e) {
        console.error("Error parsing trade time:", timeStr, e);
        return null;
      }
    };

    // Format trade execution markers
    const normalizeSide = (s: string) => {
      const upper = s?.toUpperCase() || '';
      if (upper === 'BUY' || upper === 'LONG') return 'LONG';
      if (upper === 'SELL' || upper === 'SHORT') return 'SHORT';
      return upper;
    };

    const markers: any[] = [];
    trades.forEach((trade) => {
      const side = normalizeSide(trade.side);
      const isLong = side === 'LONG';

      // 1. Entry Marker
      const entryTime = formatTime(trade.entry_time, isIntraday);
      if (entryTime) {
        markers.push({
          time: entryTime,
          position: isLong ? 'belowBar' : 'aboveBar',
          color: isLong ? '#10b981' : '#ef4444', // Green for buy, Red for short
          shape: isLong ? 'arrowUp' : 'arrowDown',
          text: isLong ? 'Buy' : 'Short',
          size: 1,
        });
      }

      // 2. Exit Marker
      if (trade.exit_time) {
        const exitTime = formatTime(trade.exit_time, isIntraday);
        if (exitTime) {
          markers.push({
            time: exitTime,
            position: isLong ? 'aboveBar' : 'belowBar',
            color: isLong ? '#f97316' : '#3b82f6', // Orange for exit long, Blue for cover short
            shape: isLong ? 'arrowDown' : 'arrowUp',
            text: isLong ? 'Exit' : 'Cover',
            size: 1,
          });
        }
      }
    });

    // Sort markers by time ascending (mandatory for lightweight-charts)
    markers.sort((a, b) => {
      if (typeof a.time === 'number' && typeof b.time === 'number') {
        return a.time - b.time;
      }
      return new Date(a.time).getTime() - new Date(b.time).getTime();
    });

    // Create Lightweight Chart instance
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#64748b',
        fontFamily: 'Inter, system-ui, sans-serif',
      },
      grid: {
        vertLines: { color: '#f1f5f9' },
        horzLines: { color: '#f1f5f9' },
      },
      crosshair: {
        mode: 1, // Magnet mode
      },
      rightPriceScale: {
        borderColor: '#e2e8f0',
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      timeScale: {
        borderColor: '#e2e8f0',
        timeVisible: true,
        secondsVisible: false,
      },
      width: chartContainerRef.current.clientWidth,
      height: 350,
    });

    // Add Candlestick Series
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    candlestickSeries.setData(formattedData as any);

    // Apply markers to candlestick series if any exist
    if (markers.length > 0) {
      createSeriesMarkers(candlestickSeries, markers);
    }

    // Fit content inside the viewport
    chart.timeScale().fitContent();

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [ohlcData, trades, timeframe]);

  return (
    <div className="w-full relative">
      <div ref={chartContainerRef} className="w-full h-[350px]" />
    </div>
  );
}

```

## frontend/src/components/charts/DrawdownChart.tsx
```tsx
import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface DrawdownChartProps {
  data: { time: string; drawdown: number }[];
}

export default function DrawdownChart({ data }: DrawdownChartProps) {
  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
          <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
          <YAxis domain={[(dataMin: any) => Math.floor(Math.min(dataMin * 1.1, -1)), 0]} tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} tickFormatter={(val) => `${val}%`} />
          <Tooltip 
            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            labelStyle={{ fontWeight: 'bold', color: '#0f172a' }}
          />
          <Area type="monotone" dataKey="drawdown" stroke="#ef4444" fill="#fee2e2" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

```

## frontend/src/components/charts/Gauge.tsx
```tsx
import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface GaugeProps {
  value: number;
  min?: number;
  max?: number;
  title: string;
  unit?: string;
  color?: string;
}

export default function Gauge({ value, min = 0, max = 100, title, unit = '', color = '#10B981' }: GaugeProps) {
  // Normalize value between min and max
  const normalizedValue = Math.min(Math.max(value, min), max);
  const percentage = ((normalizedValue - min) / (max - min)) * 100;
  
  const data = [
    { name: 'Value', value: percentage },
    { name: 'Empty', value: 100 - percentage }
  ];

  const cx = "50%";
  const cy = "75%";
  const iR = "60%";
  const oR = "80%";

  return (
    <div className="flex flex-col items-center justify-center relative h-32 w-full">
      <div className="absolute top-0 left-0 w-full h-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx={cx}
              cy={cy}
              startAngle={180}
              endAngle={0}
              innerRadius={iR}
              outerRadius={oR}
              stroke="none"
              dataKey="value"
            >
              <Cell key="cell-0" fill={color} />
              <Cell key="cell-1" fill="#E2E8F0" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="absolute bottom-2 flex flex-col items-center">
        <span className="text-2xl font-black font-industrial text-slate-900">{value.toFixed(1)}{unit}</span>
      </div>
    </div>
  );
}

```

## frontend/src/components/dashboard/MetricCards.tsx
```tsx
import React from 'react';
import { Database, LineChart, Activity } from 'lucide-react';

export default function MetricCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="bg-white border border-gray-200 p-6 rounded-2xl shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600">
            <Database className="text-xl" size={20} />
          </div>
          <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">+2 this week</span>
        </div>
        <p className="text-sm font-medium text-gray-500">Total Strategies</p>
        <h3 className="text-3xl font-bold text-gray-900 mt-1">24</h3>
      </div>

      <div className="bg-white border border-gray-200 p-6 rounded-2xl shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="w-10 h-10 bg-indigo-50 rounded-lg flex items-center justify-center text-indigo-600">
            <LineChart className="text-xl" size={20} />
          </div>
          <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded-full">99.8% Accuracy</span>
        </div>
        <p className="text-sm font-medium text-gray-500">Total Backtests</p>
        <h3 className="text-3xl font-bold text-gray-900 mt-1">142</h3>
      </div>

      <div className="bg-white border border-gray-200 p-6 rounded-2xl shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="w-10 h-10 bg-emerald-50 rounded-lg flex items-center justify-center text-emerald-600">
            <Activity className="text-xl" size={20} />
          </div>
          <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">Live</span>
        </div>
        <p className="text-sm font-medium text-gray-500">Active Deployments</p>
        <h3 className="text-3xl font-bold text-gray-900 mt-1">08</h3>
      </div>
    </div>
  );
}

```

## frontend/src/components/dashboard/RecentActivity.tsx
```tsx
/**
 * Fix 7: Dashboard status accuracy.
 * - Removed index-based status inference (no fake Live/Paused states).
 * - Uses only persisted status values from storage.
 * - Valid statuses: completed, backtested, draft, failed, unknown.
 */
"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getStrategyHistory, getBacktests } from '@/services/api';
import { Loader2, Activity, CheckCircle, AlertCircle, FileJson, HelpCircle, XCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface ActivityItem {
  id: string | number;
  type: 'backtest' | 'strategy';
  name: string;
  subname: string;
  status: string;
  statusType: 'completed' | 'backtested' | 'draft' | 'failed' | 'unknown';
  asset: string;
  pnl?: number | null;
  time: Date;
}

export default function RecentActivity() {
  const router = useRouter();
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchActivities = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch both datasets concurrently with limit=5
        const [strategiesResponse, backtestsResponse] = await Promise.all([
          getStrategyHistory(5, 0).catch(() => ({ status: 'error', strategies: [] })),
          getBacktests(5, 0).catch(() => ({ data: [], has_more: false }))
        ]);

        const items: ActivityItem[] = [];

        // 1. Process Strategy Runs
        if (strategiesResponse && strategiesResponse.status === 'ok') {
          strategiesResponse.strategies.forEach((strat: any) => {
            const date = new Date(strat.created_at);
            if (isNaN(date.getTime())) return;

            let statusText = "Draft";
            let statusType: ActivityItem['statusType'] = 'draft';

            if (strat.status === 'ok') {
              statusText = "Draft";
              statusType = 'draft';
            } else if (strat.status === 'error') {
              statusText = "Failed";
              statusType = 'failed';
            } else {
              // blocked, semantic_approval, pending, etc.
              statusText = "Incomplete";
              statusType = 'unknown';
            }

            const promptPreview = strat.prompt.length > 40
              ? strat.prompt.substring(0, 40) + '...'
              : strat.prompt;

            const ctx = strat.execution_context || strat.canonical_json?.execution_context;
            const universeIndex = ctx?.universe?.index || 'NIFTY 50';
            const assetClass = ctx?.universe?.asset_class || 'equity';
            const assetName = assetClass === 'futures' && ctx?.future_contract?.underlying 
              ? `${ctx.future_contract.underlying} FUT` 
              : universeIndex.replace('_', ' ');

            items.push({
              id: strat.id,
              type: 'strategy',
              name: promptPreview,
              subname: "Natural Language Prompt",
              status: statusText,
              statusType: statusType,
              asset: assetName,
              pnl: null,
              time: date
            });
          });
        }

        // 2. Process Backtests
        if (backtestsResponse && backtestsResponse.data) {
          backtestsResponse.data.forEach((bt: any) => {
            const date = new Date(bt.created_at);
            if (isNaN(date.getTime())) return;

            // Fix 7: Map only from persisted bt.status — never infer from index
            let statusText = "Backtested";
            let statusType: ActivityItem['statusType'] = 'backtested';

            if (bt.status === 'ok' || bt.status === 'completed') {
              statusText = "Backtested";
              statusType = 'backtested';
            } else if (bt.status === 'error' || bt.status === 'failed') {
              statusText = "Failed";
              statusType = 'failed';
            } else {
              statusText = "Unknown";
              statusType = 'unknown';
            }

            items.push({
              id: bt.id,
              type: 'backtest',
              name: bt.symbol.replace('.NS', '').replace('.BO', '') + ` Backtest`,
              subname: `Timeframe: ${bt.timeframe}`,
              status: statusText,
              statusType: statusType,
              asset: bt.symbol.replace('.NS', '').replace('.BO', ''),
              pnl: bt.net_profit,
              time: date
            });
          });
        }

        // Sort combined list by time descending
        items.sort((a, b) => b.time.getTime() - a.time.getTime());

        // Slice to display only the last 5 activities
        setActivities(items.slice(0, 5));
      } catch (err: any) {
        console.error("Error loading recent activities:", err);
        setError("Failed to load recent activities");
      } finally {
        setLoading(false);
      }
    };

    fetchActivities();
  }, []);

  const handleRowClick = (item: ActivityItem) => {
    if (item.type === 'backtest') {
      router.push(`/backtest/${item.id}`);
    } else {
      router.push(`/history?id=${item.id}`);
    }
  };

  // Fix 7: Only truthful status badges — no Live/Paused
  const getStatusBadge = (type: ActivityItem['statusType']) => {
    switch (type) {
      case 'completed':
      case 'backtested':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-bold tracking-widest uppercase bg-blue-500 text-white shadow-sm font-industrial">
            <CheckCircle className="w-3.5 h-3.5 text-white" />
            Backtested
          </span>
        );
      case 'draft':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-bold tracking-widest uppercase bg-slate-400 text-white shadow-sm font-industrial">
            <FileJson className="w-3.5 h-3.5 text-white" />
            Draft
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-bold tracking-widest uppercase bg-rose-500 text-white shadow-sm font-industrial">
            <XCircle className="w-3.5 h-3.5 text-white" />
            Failed
          </span>
        );
      case 'unknown':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-bold tracking-widest uppercase bg-gray-400 text-white shadow-sm font-industrial">
            <HelpCircle className="w-3.5 h-3.5 text-white" />
            Unknown
          </span>
        );
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(value);
  };

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-2xl p-8 flex flex-col items-center justify-center shadow-sm h-64">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin mb-3" />
        <p className="text-gray-500 text-sm">Fetching recent activity...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm flex flex-col items-center justify-center h-64 text-center">
        <AlertCircle className="w-8 h-8 text-rose-500 mb-3" />
        <h3 className="font-bold text-gray-900 text-sm">Error Loading Activity</h3>
        <p className="text-gray-500 text-xs mt-1">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
      <div className="px-6 py-5 border-b border-gray-100 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Activity className="w-5 h-5 text-gray-500" />
          Recent Activity
        </h2>
        <button
          onClick={() => router.push('/backtest')}
          className="text-sm text-blue-600 font-medium hover:underline hover:text-blue-700"
        >
          View all activity
        </button>
      </div>

      <div className="overflow-x-auto">
        {activities.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-400">
            No recent activity found. Generate a strategy or run a backtest to get started!
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50/50 text-[10px] font-bold text-gray-400 uppercase tracking-wider border-b border-gray-150">
                <th className="px-6 py-4">Strategy / Action</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Asset</th>
                <th className="px-6 py-4">P&L</th>
                <th className="px-6 py-4 text-right">Time Ago</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {activities.map((item, idx) => {
                const hasPnl = item.pnl != null;
                const pnlPositive = hasPnl && item.pnl! >= 0;

                return (
                  <tr
                    key={idx}
                    onClick={() => handleRowClick(item)}
                    className="hover:bg-slate-50/80 cursor-pointer transition-colors group"
                  >
                    <td className="px-6 py-6">
                      <div className="flex flex-col">
                        <span className="text-sm font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                          {item.name}
                        </span>
                        <span className="text-xs text-gray-500 font-medium mt-0.5">
                          {item.subname}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-6">
                      {getStatusBadge(item.statusType)}
                    </td>
                    <td className="px-6 py-6 text-sm text-gray-600 font-medium">
                      {item.asset}
                    </td>
                    <td className="px-6 py-6">
                      {hasPnl ? (
                        <span className={`text-sm font-bold font-mono ${pnlPositive ? 'text-emerald-600' : 'text-rose-600'}`}>
                          {pnlPositive ? '+' : ''}{formatCurrency(item.pnl!)}
                        </span>
                      ) : (
                        <span className="text-sm font-medium text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-6 text-right text-xs text-gray-400 font-medium">
                      {formatDistanceToNow(item.time, { addSuffix: true })}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

```

## frontend/src/components/dashboard/WelcomeSection.tsx
```tsx
import React from 'react';
import Link from 'next/link';
import { Download, Plus } from 'lucide-react';

export default function WelcomeSection() {
  return (
    <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Welcome back, Krish</h1>
        <p className="text-gray-500 mt-1">Ready to build and test new algorithmic strategies.</p>
      </div>
      <div className="flex gap-3">
        <button className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors shadow-sm">
          <Download size={18} />
          Export Logs
        </button>
        <Link href="/strategy" className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 rounded-lg text-sm font-medium text-white hover:bg-blue-700 transition-colors shadow-sm">
          <Plus size={18} />
          New Strategy
        </Link>
      </div>
    </div>
  );
}

```

## frontend/src/components/dashboard/QuickActions.tsx
```tsx
import React from 'react';
import Link from 'next/link';
import { Sparkles, ArrowRight } from 'lucide-react';

export default function QuickActions() {
  return (
    <div className="my-8">
      <Link 
        id="qa-create" 
        href="/strategy" 
        className="group relative block w-full overflow-hidden rounded-2xl bg-[#0F172A] border border-slate-700/50 hover:border-yellow-400 p-8 md:p-12 transition-all duration-500 shadow-[0_10px_40px_rgba(15,23,42,0.3)] hover:shadow-[0_0_30px_rgba(234,179,8,0.2)] hover:-translate-y-1"
      >
        {/* Background glow effects */}
        <div className="absolute top-0 right-0 -mt-16 -mr-16 w-64 h-64 bg-yellow-400/10 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
        <div className="absolute bottom-0 left-0 -mb-16 -ml-16 w-64 h-64 bg-teal-400/10 rounded-full blur-3xl opacity-50 group-hover:opacity-100 transition-opacity duration-700"></div>

        <div className="relative flex flex-col md:flex-row items-center justify-between gap-6 md:gap-10">
          
          <div className="flex items-center gap-6">
            <div className="w-16 h-16 shrink-0 bg-yellow-400/10 border border-yellow-400/30 rounded-2xl flex items-center justify-center text-yellow-400 group-hover:bg-yellow-400 group-hover:text-slate-900 group-hover:scale-110 transition-all duration-500 shadow-[0_0_15px_rgba(234,179,8,0.2)]">
              <Sparkles className="text-3xl" size={32} />
            </div>
            
            <div className="text-left">
              <h4 className="text-2xl md:text-3xl font-black text-white font-industrial tracking-wide group-hover:text-yellow-400 transition-colors">
                CREATE NEW STRATEGY
              </h4>
              <p className="text-sm md:text-base text-slate-400 mt-2 max-w-xl leading-relaxed">
                Prompt our AI engine to instantly generate, compile, and structure robust algorithmic trading logic from natural language.
              </p>
            </div>
          </div>

          <div className="shrink-0 flex items-center justify-center w-12 h-12 rounded-full bg-slate-800 text-slate-400 group-hover:bg-yellow-400 group-hover:text-slate-900 transition-all duration-500">
            <ArrowRight size={24} className="group-hover:translate-x-1 transition-transform" />
          </div>
          
        </div>
      </Link>
    </div>
  );
}

```

## frontend/src/components/controls/DynamicParametersPanel.tsx
```tsx
/**
 * Fix 4: Removed saveBacktest() — backend is single source of truth.
 *        Uses backtest_id from backend response to navigate.
 * Fix 5: Client-side validation mirroring backend rules (UX only).
 */
import React, { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { runBacktest } from '@/services/api';
import { RefreshCw } from 'lucide-react';

const ALLOWED_TIMEFRAMES = ['1m', '2m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo'];
const ALLOWED_SIZING_MODES = ['fixed_qty', 'percent_equity'];

interface DynamicParametersPanelProps {
  initialParams?: any;
  strategyAst?: any;
}

export default function DynamicParametersPanel({ initialParams, strategyAst }: DynamicParametersPanelProps) {
  const router = useRouter();

  const [localParams, setLocalParams] = useState({
    symbol: initialParams?.symbol || 'RELIANCE',
    exchange: initialParams?.exchange || 'NSE',
    timeframe: initialParams?.timeframe || '1d',
    initial_cash: initialParams?.initial_cash || 100000,
    position_size: initialParams?.position_size || 10,
    position_size_type: initialParams?.position_size_type || 'fixed_qty',
    commission_rate: initialParams?.commission_rate ?? 0.0001,
    slippage_bps: initialParams?.slippage_bps ?? 2.0,
    allow_short: initialParams?.allow_short || false,
    start_date: initialParams?.start_date || '2023-01-01',
    end_date: initialParams?.end_date || '2023-12-31',
    market_type: initialParams?.market_type || 'equity',
    position_side: initialParams?.position_side || null,
    multiplier: initialParams?.multiplier || null,
    margin: initialParams?.margin || null,
    expiry: initialParams?.expiry || null,
    strategy_id: initialParams?.strategy_id || null,
  });

  const [isRunning, setIsRunning] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleUpdate = (field: string, value: any) => {
    setLocalParams((prev: any) => ({ ...prev, [field]: value }));
  };

  // Fix 5: Client-side validation mirroring backend rules
  const validationErrors = useMemo(() => {
    const errors: string[] = [];
    if (!localParams.start_date || !localParams.end_date) errors.push('Dates are required');
    else if (new Date(localParams.start_date) >= new Date(localParams.end_date)) errors.push('Start date must be before end date');
    if (localParams.initial_cash <= 0) errors.push('Initial cash must be positive');
    if (localParams.position_size <= 0) errors.push('Position size must be positive');
    if (localParams.commission_rate < 0) errors.push('Commission rate must be non-negative');
    if (localParams.slippage_bps < 0) errors.push('Slippage must be non-negative');
    if (!ALLOWED_TIMEFRAMES.includes(localParams.timeframe?.toLowerCase())) errors.push('Invalid timeframe');
    if (!ALLOWED_SIZING_MODES.includes(localParams.position_size_type)) errors.push('Invalid sizing mode');
    if (!localParams.symbol?.trim()) errors.push('Symbol is required');
    return errors;
  }, [localParams]);

  const isValid = validationErrors.length === 0;

  const handleReRun = async () => {
    if (!strategyAst) {
      setValidationError("Missing strategy context. Cannot re-run.");
      return;
    }

    if (!isValid) {
      setValidationError(validationErrors[0]);
      return;
    }

    setIsRunning(true);
    setValidationError(null);

    try {
      const fullParams = {
        ...localParams,
        initial_capital: localParams.initial_cash || 100000,
        strategy_ast: strategyAst
      };

      // Fix 4: Backend persists the backtest and returns backtest_id
      const result = await runBacktest(fullParams);

      // Fix 4: Navigate using the durable backend ID — no saveBacktest() call
      if (result.backtest_id) {
        router.replace(`/backtest/${result.backtest_id}`);
      }
    } catch (err: any) {
      console.error("Backtest failed", err);
      setValidationError(err.message || 'Backtest failed. Check console for details.');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-900">Dynamic Parameters</h3>
      </div>

      {validationError && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-2 text-xs text-red-700">
          {validationError}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Symbol & Exchange</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={localParams.symbol || ''}
              onChange={(e) => handleUpdate('symbol', e.target.value)}
              className="w-1/2 lg:w-2/3 text-xs border rounded p-2"
            />
            <select
              value={localParams.exchange || 'NSE'}
              onChange={(e) => handleUpdate('exchange', e.target.value)}
              className="w-1/2 lg:w-1/3 text-xs border rounded p-2 bg-white"
            >
              <option value="NSE">NSE</option>
              <option value="BSE">BSE</option>
            </select>
          </div>
        </div>
        <div>
          <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Timeframe</label>
          <select
            value={localParams.timeframe || '1d'}
            onChange={(e) => handleUpdate('timeframe', e.target.value)}
            className="w-full text-xs border rounded p-2 bg-white"
          >
            {ALLOWED_TIMEFRAMES.map(tf => (
              <option key={tf} value={tf}>{tf}</option>
            ))}
          </select>
        </div>
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Initial Cash</label>
          <input
            type="number"
            value={localParams.initial_cash}
            onChange={(e) => handleUpdate('initial_cash', parseFloat(e.target.value))}
            className="w-full px-3 py-2 bg-white border border-slate-200 rounded-md text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all font-mono"
          />
        </div>
        <div>
          <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Position Size</label>
          <div className="flex gap-2">
            <input
              type="number"
              value={localParams.position_size || 10}
              onChange={(e) => handleUpdate('position_size', parseFloat(e.target.value))}
              min={0}
              className="w-2/3 text-xs border rounded p-2"
            />
            <select
              value={localParams.position_size_type || 'fixed_qty'}
              onChange={(e) => handleUpdate('position_size_type', e.target.value)}
              className="w-1/3 text-xs border rounded p-2 bg-white"
            >
              <option value="fixed_qty">Qty</option>
              <option value="percent_equity">% Eq</option>
            </select>
          </div>
        </div>
        <div>
          <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Start Date</label>
          <input
            type="date"
            value={localParams.start_date || ''}
            onChange={(e) => handleUpdate('start_date', e.target.value)}
            className="w-full text-xs border rounded p-2 bg-white"
          />
        </div>
        <div>
          <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">End Date</label>
          <input
            type="date"
            value={localParams.end_date || ''}
            onChange={(e) => handleUpdate('end_date', e.target.value)}
            className="w-full text-xs border rounded p-2 bg-white"
          />
        </div>
        <div>
          <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Commission</label>
          <input
            type="number"
            value={localParams.commission_rate}
            onChange={(e) => handleUpdate('commission_rate', parseFloat(e.target.value))}
            min={0}
            step={0.0001}
            className="w-full text-xs border rounded p-2"
          />
        </div>
        <div>
          <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Slippage (bps)</label>
          <input
            type="number"
            value={localParams.slippage_bps}
            onChange={(e) => handleUpdate('slippage_bps', parseFloat(e.target.value))}
            min={0}
            step={0.1}
            className="w-full text-xs border rounded p-2"
          />
        </div>
        <div className="flex items-center gap-2 mt-5">
          <input
            type="checkbox"
            checked={localParams.allow_short || false}
            onChange={(e) => handleUpdate('allow_short', e.target.checked)}
            id="allowShortDynamic"
          />
          <label htmlFor="allowShortDynamic" className="text-xs font-bold text-slate-700">Allow Shorting</label>
        </div>
        <div className="flex items-end">
          <button
            onClick={handleReRun}
            disabled={isRunning || !isValid}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-bold shadow-sm hover:bg-slate-800 disabled:opacity-50"
          >
            {isRunning ? <RefreshCw className="animate-spin" size={14} /> : null}
            Re-run Backtest
          </button>
        </div>
      </div>
    </div>
  );
}

```

## frontend/src/components/strategy/AssumptionBox.tsx
```tsx
"use client";
import React, { useState } from 'react';
import { CheckCircle2 } from 'lucide-react';

interface Option {
  id: string;
  label: string;
}

interface AssumptionBoxProps {
  title: string;
  aiSelectedLabel: string;
  options: Option[];
  name: string;
}

export default function AssumptionBox({ title, aiSelectedLabel, options, name }: AssumptionBoxProps) {
  const [selected, setSelected] = useState<string>(options[0].id);

  return (
    <div className="assumption-box">
      <h4 className="text-2xl font-bold text-gray-900 mb-8">{title}</h4>
      <div className="flex flex-col items-start gap-4">
        <div className="ai-badge">
          <CheckCircle2 size={24} /> {aiSelectedLabel} (AI Selected)
        </div>
        <div className="radio-group">
          {options.map((opt) => (
            <div className="radio-option" key={opt.id}>
              <input 
                type="radio" 
                id={opt.id} 
                name={name} 
                className="radio-input hidden" 
                checked={selected === opt.id}
                onChange={() => setSelected(opt.id)}
              />
              <label htmlFor={opt.id} className="radio-label">
                <div className="radio-custom-circle">
                  <div className="radio-inner-dot"></div>
                </div>
                <span className="font-semibold">{opt.label}</span>
              </label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

```

## frontend/src/components/strategy/ExecutionContextForm.tsx
```tsx
"use client";
import React from 'react';

const INDEX_OPTIONS = [
  { value: 'NIFTY_50', label: 'NIFTY 50' },
  { value: 'NIFTY_BANK', label: 'BANK NIFTY' },
  { value: 'NIFTY_IT', label: 'NIFTY IT' },
  { value: 'NIFTY_NEXT_50', label: 'NIFTY NEXT 50' },
  { value: 'SENSEX', label: 'SENSEX' },
];

const TIMEFRAME_OPTIONS = [
  '1m', '2m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo'
];

const STOCK_OPTIONS = [
  { value: 'RELIANCE', label: 'RELIANCE FUT' },
  { value: 'TCS', label: 'TCS FUT' },
  { value: 'HDFCBANK', label: 'HDFCBANK FUT' },
  { value: 'INFY', label: 'INFY FUT' },
  { value: 'HDFC', label: 'HDFC FUT' },
  { value: 'ICICIBANK', label: 'ICICIBANK FUT' },
  { value: 'KOTAKBANK', label: 'KOTAKBANK FUT' },
  { value: 'HINDUNILVR', label: 'HINDUNILVR FUT' },
  { value: 'BHARTIARTL', label: 'BHARTIARTL FUT' },
  { value: 'SBIN', label: 'SBIN FUT' },
  { value: 'AXISBANK', label: 'AXISBANK FUT' },
  { value: 'LT', label: 'LT FUT' },
  { value: 'ITC', label: 'ITC FUT' },
  { value: 'BAJFINANCE', label: 'BAJFINANCE FUT' },
  { value: 'MARUTI', label: 'MARUTI FUT' },
  { value: 'TITAN', label: 'TITAN FUT' },
  { value: 'BAJAJFINSV', label: 'BAJAJFINSV FUT' },
  { value: 'SUNPHARMA', label: 'SUNPHARMA FUT' },
  { value: 'JSWSTEEL', label: 'JSWSTEEL FUT' },
  { value: 'ONGC', label: 'ONGC FUT' },
  { value: 'ULTRACEMCO', label: 'ULTRACEMCO FUT' },
  { value: 'NTPC', label: 'NTPC FUT' },
  { value: 'POWERGRID', label: 'POWERGRID FUT' },
  { value: 'TATASTEEL', label: 'TATASTEEL FUT' },
  { value: 'NESTLEIND', label: 'NESTLEIND FUT' },
  { value: 'TATAMOTORS', label: 'TATAMOTORS FUT' },
  { value: 'HCLTECH', label: 'HCLTECH FUT' },
  { value: 'ADANIENT', label: 'ADANIENT FUT' },
  { value: 'ASIANPAINT', label: 'ASIANPAINT FUT' },
  { value: 'WIPRO', label: 'WIPRO FUT' },
  { value: 'EICHERMOT', label: 'EICHERMOT FUT' },
  { value: 'HINDALCO', label: 'HINDALCO FUT' },
  { value: 'COALINDIA', label: 'COALINDIA FUT' },
  { value: 'BRITANNIA', label: 'BRITANNIA FUT' },
  { value: 'DIVISLAB', label: 'DIVISLAB FUT' },
  { value: 'HINDZINC', label: 'HINDZINC FUT' },
  { value: 'BPCL', label: 'BPCL FUT' },
  { value: 'HINDPETRO', label: 'HINDPETRO FUT' },
  { value: 'TATACONSUM', label: 'TATACONSUM FUT' },
  { value: 'GRASIM', label: 'GRASIM FUT' },
  { value: 'DRREDDY', label: 'DRREDDY FUT' },
  { value: 'TECHM', label: 'TECHM FUT' },
  { value: 'SBILIFE', label: 'SBILIFE FUT' },
  { value: 'SHREECEM', label: 'SHREECEM FUT' },
  { value: 'TATACHEM', label: 'TATACHEM FUT' },
  { value: 'M&M', label: 'M&M FUT' },
  { value: 'GAIL', label: 'GAIL FUT' },
  { value: 'INDUSINDBK', label: 'INDUSINDBK FUT' },
];

interface ExecutionContextFormProps {
  context: {
    universe: {
      index: string;
      exchange: string;
      asset_class: string;
    };
    timeframe: string;
    capital_per_trade: {
      amount: number;
      currency: string;
    };
    position_side: string;
    order_type: string;
    max_concurrent_positions: number;
    stock: string;
    future_contract?: {
      underlying: string;
      expiry: string;
      lot_size: number;
      margin: number;
    };
  };
  setContext: React.Dispatch<React.SetStateAction<any>>;
}

export default function ExecutionContextForm({ context, setContext }: ExecutionContextFormProps) {
  const isEquity = context.universe.asset_class !== 'futures'; // Treat 'equity' or empty as Equity, 'futures' as Future

  return (
    <section className="lg:col-span-4 bg-white border border-gray-200 rounded-2xl shadow-md hover:shadow-lg transition-shadow duration-300 overflow-hidden relative z-10">
      <div className="p-6 border-b border-gray-100">
        <h2 className="text-base font-bold text-gray-900">Execution Context</h2>
        <p className="text-xs text-gray-500 mt-0.5">Operational constraints for this strategy.</p>
      </div>
      <div className="p-6 space-y-6">
        {/* Prominent Toggle Switch */}
        <div className="bg-gray-50 p-1 rounded-lg flex border border-gray-100">
          <button
            onClick={() => setContext({ ...context, universe: { ...context.universe, asset_class: 'equity' } })}
            className={`flex-1 py-2 text-xs font-semibold rounded-md transition-all duration-200 uppercase tracking-wider ${
              isEquity 
                ? 'bg-white text-blue-600 shadow border border-gray-200' 
                : 'text-gray-400 hover:text-gray-600'
            }`}
          >
            Equity Trade
          </button>
          <button
            onClick={() => setContext({ ...context, universe: { ...context.universe, asset_class: 'futures' } })}
            className={`flex-1 py-2 text-xs font-semibold rounded-md transition-all duration-200 uppercase tracking-wider ${
              !isEquity 
                ? 'bg-white text-purple-600 shadow border border-gray-200' 
                : 'text-gray-400 hover:text-gray-600'
            }`}
          >
            Future Trade
          </button>
        </div>

        {isEquity ? (
          /* EQUITY FIELDS */
          <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
            <div>
              <label className="label-text">Index</label>
              <select
                value={context.universe.index}
                onChange={(e) => setContext({
                  ...context,
                  universe: { ...context.universe, index: e.target.value }
                })}
                className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="" disabled>Select an index</option>
                {INDEX_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label-text">Exchange</label>
                <select 
                  value={context.universe.exchange}
                  onChange={(e) => setContext({
                    ...context,
                    universe: { ...context.universe, exchange: e.target.value }
                  })}
                  className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="" disabled>Select Exchange</option>
                  <option value="NSE">NSE</option>
                  <option value="BSE">BSE</option>
                </select>
              </div>
              <div>
                <label className="label-text">Asset Class</label>
                <select 
                  value={context.universe.asset_class}
                  onChange={(e) => setContext({
                    ...context,
                    universe: { ...context.universe, asset_class: e.target.value }
                  })}
                  className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="" disabled>Select Asset Class</option>
                  <option value="equity">Equity</option>
                  <option value="futures">Futures</option>
                </select>
              </div>
            </div>
            <div>
              <label className="label-text">Timeframe</label>
              <div className="flex flex-wrap gap-2 p-2 bg-gray-50 rounded-lg border border-gray-100">
                {TIMEFRAME_OPTIONS.map(tf => (
                  <button
                    key={tf}
                    onClick={() => setContext({ ...context, timeframe: tf })}
                    className={`py-1.5 px-3 text-xs rounded-md shadow-sm border transition-colors whitespace-nowrap ${
                      context.timeframe === tf 
                        ? 'font-semibold bg-white border-gray-200 text-blue-600' 
                        : 'font-medium border-transparent text-gray-500 hover:text-gray-900 bg-white border border-gray-200'
                    }`}
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label-text">Capital / Trade</label>
                <input 
                  type="text" 
                  value={context.capital_per_trade.amount || ''}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value.replace(/[^0-9.]/g, '')) || 0;
                    setContext({
                      ...context,
                      capital_per_trade: { ...context.capital_per_trade, amount: val }
                    });
                  }}
                  className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-blue-500" 
                />
              </div>
              <div>
                <label className="label-text">Order Type</label>
                <select 
                  value={context.order_type}
                  onChange={(e) => setContext({ ...context, order_type: e.target.value })}
                  className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="" disabled>Select Order Type</option>
                  <option value="MARKET">MARKET</option>
                  <option value="LIMIT">LIMIT</option>
                </select>
              </div>
            </div>
            <div>
              <label className="label-text">Stock</label>
              <select
                value={context.stock}
                onChange={(e) => setContext({ ...context, stock: e.target.value })}
                className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="" disabled>Select Stock</option>
                {STOCK_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {context.universe.asset_class === 'equity' 
                      ? option.label.replace(' FUT', '') 
                      : option.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label-text">Position Side</label>
              <div className="flex gap-2">
                <button 
                  onClick={() => setContext({ ...context, position_side: 'LONG' })}
                  className={`flex-1 py-2 text-xs rounded-lg transition-colors ${
                    context.position_side === 'LONG' 
                      ? 'font-bold border-2 border-blue-600 text-blue-600' 
                      : 'font-medium bg-gray-50 text-gray-400 border border-gray-100 hover:border-gray-200 hover:text-gray-600'
                  }`}
                >
                  LONG
                </button>
                <button 
                  onClick={() => setContext({ ...context, position_side: 'SHORT' })}
                  className={`flex-1 py-2 text-xs rounded-lg transition-colors ${
                    context.position_side === 'SHORT' 
                      ? 'font-bold border-2 border-blue-600 text-blue-600' 
                      : 'font-medium bg-gray-50 text-gray-400 border border-gray-100 hover:border-gray-200 hover:text-gray-600'
                  }`}
                >
                  SHORT
                </button>
              </div>
            </div>
            <div>
              <label className="label-text">Max Concurrent Positions</label>
              <input 
                type="number" 
                value={context.max_concurrent_positions || ''}
                onChange={(e) => setContext({ ...context, max_concurrent_positions: parseInt(e.target.value, 10) || 0 })}
                className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-blue-500" 
              />
            </div>
          </div>
        ) : (
          /* FUTURES FIELDS */
          <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label-text">Underlying Asset</label>
                <select
                  value={context.future_contract?.underlying || ''}
                  onChange={(e) => setContext({ 
                    ...context, 
                    future_contract: { ...(context.future_contract || {}), underlying: e.target.value }
                  })}
                  className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-purple-500 transition-all"
                >
                  <option value="" disabled>Select Underlying Asset</option>
                  <optgroup label="Index Futures">
                    {INDEX_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </optgroup>
                  <optgroup label="Stock Futures">
                    {STOCK_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </optgroup>
                </select>
              </div>

              <div>
                <label className="label-text">Mode</label>
                <div className="w-full px-3 py-2 bg-purple-50 text-purple-800 border border-purple-200 rounded-lg text-sm font-medium flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></span>
                  Continuous (Auto-Spliced)
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label-text">Number of Lots</label>
                <input 
                  type="number" 
                  value={context.future_contract?.lot_size || ''}
                  onChange={(e) => setContext({ 
                    ...context, 
                    future_contract: { ...(context.future_contract || {}), lot_size: parseInt(e.target.value, 10) || 0 }
                  })}
                  placeholder="e.g. 50" 
                  className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-purple-500 transition-all"
                />
              </div>
              
              <div>
                <label className="label-text">Initial Capital</label>
                <input 
                  type="text" 
                  value={context.capital_per_trade.amount || ''}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value.replace(/[^0-9.]/g, '')) || 0;
                    setContext({
                      ...context,
                      capital_per_trade: { ...context.capital_per_trade, amount: val }
                    });
                  }}
                  className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-purple-500 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="label-text">Timeframe</label>
              <div className="flex flex-wrap gap-2 p-2 bg-gray-50 rounded-lg border border-gray-100">
                {TIMEFRAME_OPTIONS.map(tf => (
                  <button
                    key={tf}
                    onClick={() => setContext({ ...context, timeframe: tf })}
                    className={`py-1.5 px-3 text-xs rounded-md shadow-sm border transition-colors whitespace-nowrap ${
                      context.timeframe === tf 
                        ? 'font-semibold bg-white border-purple-200 text-purple-600' 
                        : 'font-medium border-transparent text-gray-500 hover:text-gray-900 bg-white border border-gray-200'
                    }`}
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="label-text">Position Side</label>
              <div className="flex gap-2">
                <button 
                  onClick={() => setContext({ ...context, position_side: 'LONG' })}
                  className={`flex-1 py-2 text-xs rounded-lg transition-colors ${
                    context.position_side === 'LONG' 
                      ? 'font-bold border-2 border-purple-600 text-purple-600' 
                      : 'font-medium bg-gray-50 text-gray-400 border border-gray-100 hover:border-gray-200 hover:text-gray-600'
                  }`}
                >
                  LONG
                </button>
                <button 
                  onClick={() => setContext({ ...context, position_side: 'SHORT' })}
                  className={`flex-1 py-2 text-xs rounded-lg transition-colors ${
                    context.position_side === 'SHORT' 
                      ? 'font-bold border-2 border-purple-600 text-purple-600' 
                      : 'font-medium bg-gray-50 text-gray-400 border border-gray-100 hover:border-gray-200 hover:text-gray-600'
                  }`}
                >
                  SHORT
                </button>
                <button 
                  onClick={() => setContext({ ...context, position_side: 'BOTH' })}
                  className={`flex-1 py-2 text-xs rounded-lg transition-colors ${
                    context.position_side === 'BOTH' 
                      ? 'font-bold border-2 border-purple-600 text-purple-600' 
                      : 'font-medium bg-gray-50 text-gray-400 border border-gray-100 hover:border-gray-200 hover:text-gray-600'
                  }`}
                >
                  BOTH
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

```

## frontend/src/components/strategy/NaturalLanguageEditor.tsx
```tsx
"use client";
import React, { useState } from 'react';
import { Wand2, Sparkles, Info, AlertTriangle, CheckCircle, HelpCircle, Loader2 } from 'lucide-react';
import StrategySummary from './StrategySummary';
import BacktestConfigModal from './BacktestConfigModal';

/**
 * Fix 1: All fetch calls use relative URLs through Next.js proxy routes.
 *        No API key headers are sent from the browser.
 * Fix 6: Character counter shown below textarea. Clarification retry cap = 5.
 */

const MAX_PROMPT_LENGTH = 10000;
const MAX_CLARIFICATION_RETRIES = 5;

type Blocker = {
  reason: string;
  question: string;
};

type ApprovalItem = {
  type: string;
  source: string;
  candidates: string[];
  confidence: number;
};

type StrategyResult = {
  status: string;
  prompt: string;
  canonical_json?: Record<string, unknown>;
  ast_json?: Record<string, unknown>;
  blockers?: Blocker[];
  approval_items?: ApprovalItem[];
  current_strategy?: string;
  message?: string;
};

interface NaturalLanguageEditorProps {
  executionContext: {
    universe: {
      index: string;
      exchange: string;
      asset_class: string;
    };
    timeframe: string;
    capital_per_trade: {
      amount: number;
      currency: string;
    };
    position_side: string;
    order_type: string;
    max_concurrent_positions: number;
    stock: string;
  };
}

export default function NaturalLanguageEditor({ executionContext }: NaturalLanguageEditorProps) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | string[] | null>(null);
  const [result, setResult] = useState<StrategyResult | null>(null);

  // Loop state
  const [blockerAnswers, setBlockerAnswers] = useState<Record<string, string>>({});
  const [semanticResolutions, setSemanticResolutions] = useState<Record<string, string>>({});
  const [customSemanticInputs, setCustomSemanticInputs] = useState<Record<string, string>>({});
  const [currentStrategyText, setCurrentStrategyText] = useState('');
  const [showConfigModal, setShowConfigModal] = useState(false);
  // Fix 6: Track clarification retry count
  const [clarificationCount, setClarificationCount] = useState(0);

  const isEquity = executionContext.universe.asset_class !== 'futures';

  let isContextValid = false;
  if (isEquity) {
    isContextValid =
      executionContext.capital_per_trade.amount > 0 &&
      !!executionContext.timeframe &&
      !!executionContext.stock &&
      !!executionContext.universe.index &&
      !!executionContext.universe.exchange &&
      !!executionContext.position_side &&
      !!executionContext.order_type &&
      executionContext.max_concurrent_positions > 0;
  } else {
    isContextValid =
      executionContext.capital_per_trade.amount > 0 &&
      !!executionContext.timeframe &&
      !!executionContext.position_side &&
      !!(executionContext as any).future_contract?.underlying &&
      ((executionContext as any).future_contract?.lot_size || 0) > 0;
  }

  // Fix 6: Character counter helpers
  const remaining = MAX_PROMPT_LENGTH - content.length;
  const isOverLimit = remaining < 0;

  const resetInteractiveState = () => {
    setBlockerAnswers({});
    setSemanticResolutions({});
    setCustomSemanticInputs({});
    setCurrentStrategyText('');
    setShowConfigModal(false);
    setClarificationCount(0);
  };

  const handleGenerateStrategy = async () => {
    if (!content.trim()) {
      setError('Please enter a strategy prompt.');
      return;
    }

    // Fix 6: Client-side prompt length check
    if (content.length > MAX_PROMPT_LENGTH) {
      setError(`Prompt exceeds maximum length of ${MAX_PROMPT_LENGTH.toLocaleString()} characters.`);
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    resetInteractiveState();

    const initialPrompt = content.trim();
    setCurrentStrategyText(initialPrompt);

    try {
      // Fix 1: Route through server-side proxy — no API key in browser
      const response = await fetch('/api/proxy/strategy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: initialPrompt,
          market_type: isEquity ? 'equity' : 'futures',
          execution_context: executionContext
        }),
      });

      const text = await response.text();
      let data: any;
      try {
        data = JSON.parse(text);
      } catch (e) {
        throw new Error(`Server returned invalid response (500). Backend might be down or crashed. Raw: ${text.substring(0, 100)}...`);
      }

      if (!response.ok) {
        if (data.detail && typeof data.detail === 'object' && Array.isArray(data.detail.messages)) {
          setError(data.detail.messages);
          setLoading(false);
          return;
        }
        throw new Error(data.detail || data.message || 'Failed to generate strategy');
      }

      setResult(data);
      if (data && data.status === 'ok' && data.id) {
        // Fix 1: Route to review page with ID instead of using localStorage
        window.location.href = `/strategy/review?id=${data.id}`;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitClarifications = async () => {
    // Fix 6: Cap clarification retries
    if (clarificationCount >= MAX_CLARIFICATION_RETRIES) {
      setError(
        `Maximum clarification retries (${MAX_CLARIFICATION_RETRIES}) reached. ` +
        `Please simplify your strategy prompt and try again.`
      );
      return;
    }

    setLoading(true);
    setError(null);

    let augmented = currentStrategyText;
    const blockers = result?.blockers || [];

    blockers.forEach((b) => {
      const answer = blockerAnswers[b.question]?.trim();
      if (answer) {
        augmented += `\n\nClarification regarding '${b.question}': ${answer}`;
      }
    });

    // Fix 6: Check augmented prompt length
    if (augmented.length > MAX_PROMPT_LENGTH) {
      setError(`Augmented prompt exceeds maximum length of ${MAX_PROMPT_LENGTH.toLocaleString()} characters. Please shorten your answers.`);
      setLoading(false);
      return;
    }

    setCurrentStrategyText(augmented);
    setClarificationCount(prev => prev + 1);

    try {
      // Fix 1: Route through server-side proxy
      const response = await fetch('/api/proxy/strategy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: augmented,
          market_type: isEquity ? 'equity' : 'futures',
          execution_context: executionContext
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Failed to generate strategy');
      }

      setResult(data);
      if (data && data.status === 'ok') {
        localStorage.setItem('last_compiled_strategy', JSON.stringify({
          canonical_json: data.canonical_json,
          ast_json: data.ast_json,
          execution_context: executionContext
        }));
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitSemanticResolutions = async () => {
    // Fix 6: Cap clarification retries
    if (clarificationCount >= MAX_CLARIFICATION_RETRIES) {
      setError(
        `Maximum clarification retries (${MAX_CLARIFICATION_RETRIES}) reached. ` +
        `Please simplify your strategy prompt and try again.`
      );
      return;
    }

    setLoading(true);
    setError(null);
    setClarificationCount(prev => prev + 1);

    const approvalItems = result?.approval_items || [];
    const resolutions = approvalItems.map((item) => {
      const chosen = semanticResolutions[item.source] || item.candidates[0];
      const finalResolution = chosen === '__custom__'
        ? customSemanticInputs[item.source]?.trim() || item.candidates[0]
        : chosen;
      return {
        source: item.source,
        resolution: finalResolution,
      };
    });

    try {
      // Fix 1: Route through server-side proxy
      const response = await fetch('/api/proxy/strategy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: currentStrategyText,
          semantic_resolutions: resolutions,
          market_type: isEquity ? 'equity' : 'futures',
          execution_context: executionContext,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        if (data.detail && typeof data.detail === 'object' && Array.isArray(data.detail.messages)) {
          setError(data.detail.messages);
          setLoading(false);
          return;
        }
        throw new Error(data.detail || data.message || 'Failed to generate strategy');
      }

      setResult(data);
      if (data && data.status === 'ok' && data.id) {
        // Fix 1: Route to review page with ID instead of using localStorage
        window.location.href = `/strategy/review?id=${data.id}`;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="lg:col-span-8 space-y-6 relative z-10">
      <div className="bg-white border border-gray-200 rounded-2xl shadow-md hover:shadow-lg transition-shadow duration-300 overflow-hidden flex flex-col h-[520px]">
        <div className="p-6 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center">
              <Wand2 className="text-lg" size={18} />
            </div>
            <div>
              <h2 className="text-base font-bold text-gray-900">Natural Language Editor</h2>
              <p className="text-xs text-gray-500">Describe your strategy logic in plain English.</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded border border-emerald-100 uppercase tracking-tighter">
              <span className="w-1 h-1 bg-emerald-500 rounded-full animate-pulse"></span>
              AI Engine Ready
            </span>
          </div>
        </div>

        <div className="flex-1 p-0 relative">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                if (isContextValid && !loading && !isOverLimit) {
                  handleGenerateStrategy();
                }
              }
            }}
            disabled={loading || !isContextValid}
            maxLength={MAX_PROMPT_LENGTH + 100} // Soft limit via maxLength, hard limit via validation
            className="w-full h-full p-8 pb-12 resize-none focus:outline-none text-gray-700 text-lg leading-relaxed placeholder:text-gray-355 disabled:bg-gray-50"
            placeholder={
              !isContextValid
                ? "Please fill all execution context parameters on the left first..."
                : "Buy when RSI crosses above 30 and EMA20 is above EMA50. Exit when RSI exceeds 70.\n(Press Ctrl+Enter to generate)"
            }
          />

          {/* Fix 6: Character counter */}
          {isContextValid && (
            <div className="absolute bottom-2 left-8 right-8 flex items-center justify-between">
              <span className={`text-xs font-mono ${
                isOverLimit
                  ? 'text-red-600 font-bold'
                  : remaining < 500
                    ? 'text-amber-600 font-semibold'
                    : 'text-gray-400'
              }`}>
                {content.length.toLocaleString()} / {MAX_PROMPT_LENGTH.toLocaleString()} characters
                {remaining < 500 && remaining >= 0 && ` (${remaining} remaining)`}
                {isOverLimit && ` — ${Math.abs(remaining)} over limit`}
              </span>
              {clarificationCount > 0 && (
                <span className="text-xs text-gray-400">
                  Retries: {clarificationCount}/{MAX_CLARIFICATION_RETRIES}
                </span>
              )}
            </div>
          )}

          {!isContextValid && (
            <div className="absolute inset-0 bg-gray-50/80 backdrop-blur-[2px] flex flex-col items-center justify-center p-6 text-center z-10 transition-all duration-300">
              <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mb-4 shadow-sm border border-blue-100">
                <Info size={28} />
              </div>
              <h3 className="text-lg font-bold text-gray-900">Unlock Natural Language Editor</h3>
              <p className="text-sm text-gray-500 max-w-sm mt-2">
                Please fill all the deterministic parameters (Capital, Timeframe, Stock, etc.) in the <strong>Execution Context</strong> panel on the left to start writing your strategy.
              </p>
            </div>
          )}

          {isContextValid && (
            <div className="absolute bottom-8 right-8">
              <button
                onClick={handleGenerateStrategy}
                disabled={loading || isOverLimit}
                className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-bold shadow-lg shadow-blue-500/20 hover:bg-blue-700 transform hover:-translate-y-0.5 transition-all disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading && !result ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    Generate Strategy
                    <Sparkles className="text-lg" size={18} />
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>

      {error ? (
        <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-sm text-red-700 shadow-sm flex items-start gap-2">
          <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-red-600" />
          <div className="flex-1">
            {Array.isArray(error) ? (
              <ul className="list-disc pl-4 space-y-1">
                {error.map((err, i) => <li key={i}>{err}</li>)}
              </ul>
            ) : (
              <div>{error}</div>
            )}
          </div>
        </div>
      ) : null}

      {/* STAGE 1: Blocker Clarification Form */}
      {result && result.status === 'blocked' && result.blockers && result.blockers.length > 0 ? (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 shadow-sm space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-100 text-amber-700 rounded-xl flex items-center justify-center">
              <AlertTriangle size={20} />
            </div>
            <div>
              <h3 className="text-base font-bold text-amber-900">Clarification Required</h3>
              <p className="text-xs text-amber-700 mt-0.5">
                The AI engine needs additional details before compiling this strategy.
                {clarificationCount > 0 && (
                  <span className="ml-1 font-semibold">
                    (Attempt {clarificationCount}/{MAX_CLARIFICATION_RETRIES})
                  </span>
                )}
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {result.blockers.map((b, idx) => (
              <div key={idx} className="bg-white border border-amber-100 rounded-xl p-4 space-y-3 animate-fade-in">
                <div>
                  <span className="text-[10px] font-bold uppercase text-amber-750 bg-amber-50 px-2 py-0.5 rounded border border-amber-100">
                    Reason: {b.reason}
                  </span>
                  <h4 className="text-sm font-semibold text-gray-900 mt-2">{b.question}</h4>
                </div>
                <textarea
                  rows={2}
                  value={blockerAnswers[b.question] || ''}
                  onChange={(e) => setBlockerAnswers({ ...blockerAnswers, [b.question]: e.target.value })}
                  placeholder="Provide clarification details here..."
                  className="w-full text-sm border border-gray-200 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent text-gray-700"
                />
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={() => setResult(null)}
              className="px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmitClarifications}
              disabled={loading || clarificationCount >= MAX_CLARIFICATION_RETRIES}
              className="px-6 py-2.5 bg-amber-600 hover:bg-amber-700 text-white font-bold rounded-lg text-sm shadow-sm transition-colors disabled:opacity-50"
            >
              {loading ? 'Submitting...' : 'Submit Answers & Re-evaluate'}
            </button>
          </div>
        </div>
      ) : null}

      {/* STAGE 2: Semantic Resolver Form */}
      {result && result.status === 'semantic_approval' && result.approval_items && result.approval_items.length > 0 ? (
        <div className="bg-indigo-50 border border-indigo-200 rounded-2xl p-6 shadow-sm space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-100 text-indigo-700 rounded-xl flex items-center justify-center">
              <HelpCircle size={20} />
            </div>
            <div>
              <h3 className="text-base font-bold text-indigo-900">Resolve Ambiguous Terms</h3>
              <p className="text-xs text-indigo-700 mt-0.5">
                Confirm or override the AI interpretations for these trading terms.
                {clarificationCount > 0 && (
                  <span className="ml-1 font-semibold">
                    (Attempt {clarificationCount}/{MAX_CLARIFICATION_RETRIES})
                  </span>
                )}
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {result.approval_items.map((item, idx) => {
              const selectedValue = semanticResolutions[item.source] || item.candidates[0];
              return (
                <div key={idx} className="bg-white border border-indigo-100 rounded-xl p-5 space-y-4 animate-fade-in">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <span className="text-[10px] font-bold uppercase text-indigo-750 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
                        Ambiguous term: &quot;{item.source}&quot;
                      </span>
                      <p className="text-xs text-gray-500 mt-1">Select the correct matching parameter configuration.</p>
                    </div>
                    <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
                      Confidence: {Math.round(item.confidence * 100)}%
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <select
                      value={selectedValue}
                      onChange={(e) => setSemanticResolutions({ ...semanticResolutions, [item.source]: e.target.value })}
                      className="border border-gray-200 rounded-lg p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-700 bg-white"
                    >
                      {item.candidates.map((cand, candIdx) => (
                        <option key={candIdx} value={cand}>
                          {cand} {candIdx === 0 ? '[Default]' : ''}
                        </option>
                      ))}
                      <option value="__custom__">Write my own...</option>
                    </select>

                    {selectedValue === '__custom__' ? (
                      <input
                        type="text"
                        placeholder="Enter custom resolution (e.g. RSI > 50)"
                        value={customSemanticInputs[item.source] || ''}
                        onChange={(e) => setCustomSemanticInputs({ ...customSemanticInputs, [item.source]: e.target.value })}
                        className="border border-gray-200 rounded-lg p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-700"
                      />
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={() => setResult(null)}
              className="px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmitSemanticResolutions}
              disabled={loading || clarificationCount >= MAX_CLARIFICATION_RETRIES}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg text-sm shadow-sm transition-colors disabled:opacity-50"
            >
              {loading ? 'Submitting...' : 'Confirm Selections & Compile'}
            </button>
          </div>
        </div>
      ) : null}

      {/* STAGE 3: Successful compiled outputs */}
      {result && result.status === 'ok' ? (
        <div className="space-y-6">
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 text-sm text-emerald-800 shadow-sm flex items-start justify-between">
            <div className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 shrink-0 mt-0.5 text-emerald-600" />
              <div>
                <strong>Strategy Successfully Compiled!</strong> Your strategy logic has been parsed into our engine.
              </div>
            </div>
            <button
              onClick={() => setShowConfigModal(true)}
              className="px-4 py-2 bg-emerald-600 text-white font-bold rounded-lg shadow hover:bg-emerald-700"
            >
              Configure & Run Backtest
            </button>
          </div>
          <StrategySummary
            canonicalJson={result.canonical_json}
            executionContext={executionContext}
          />
        </div>
      ) : null}

      {showConfigModal && result?.ast_json && result?.canonical_json && (
        <BacktestConfigModal
          ast={result.ast_json}
          canonical={result.canonical_json}
          executionContext={executionContext}
          onClose={() => setShowConfigModal(false)}
        />
      )}

      <div className="bg-blue-50/50 border border-blue-100 rounded-xl p-5 flex gap-4">
        <div className="mt-1 text-blue-600">
          <Info className="text-xl" size={20} />
        </div>
        <div>
          <h4 className="text-sm font-bold text-blue-900">How it works</h4>
          <p className="text-sm text-blue-800/70 leading-relaxed mt-1">
            QuantAI&apos;s LLM interprets your trading logic and converts it into a structured JSON payload for our backtesting engine.
            Avoid ambiguity for better accuracy.
          </p>
        </div>
      </div>
    </section>
  );
}

```

## frontend/src/components/strategy/StrategyHistoryList.tsx
```tsx
"use client";

import React, { useEffect, useState } from 'react';
import { getStrategyHistory } from '@/services/api';
import { Clock, CheckCircle, XCircle, AlertCircle, HelpCircle, ChevronRight, FileJson } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface StrategyRecord {
  id: number;
  prompt: string;
  status: string;
  created_at: string;
  canonical_json: any;
  ast_json: any;
  logs: string;
}

export function StrategyHistoryList() {
  const [strategies, setStrategies] = useState<StrategyRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const fetchHistory = async (currentOffset = 0, isLoadMore = false) => {
    try {
      if (isLoadMore) setLoadingMore(true);
      else setLoading(true);
      
      const data = await getStrategyHistory(10, currentOffset);
      if (data.status === 'ok') {
        if (isLoadMore) {
          setStrategies(prev => [...prev, ...data.strategies]);
        } else {
          setStrategies(data.strategies);
        }
        setHasMore(data.has_more);
        setOffset(currentOffset);
      } else {
        setError('Failed to fetch history');
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleLoadMore = () => {
    fetchHistory(offset + 10, true);
  };

  useEffect(() => {
    if (typeof window !== 'undefined' && strategies.length > 0) {
      const params = new URLSearchParams(window.location.search);
      const strategyIdParam = params.get('id');
      if (strategyIdParam) {
        setExpandedId(Number(strategyIdParam));
      }
    }
  }, [strategies]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ok': return <CheckCircle className="w-5 h-5 text-emerald-500" />;
      case 'error': return <XCircle className="w-5 h-5 text-rose-500" />;
      case 'blocked': return <AlertCircle className="w-5 h-5 text-amber-500" />;
      case 'semantic_approval': return <HelpCircle className="w-5 h-5 text-indigo-500" />;
      default: return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'ok': return 'bg-emerald-50 text-emerald-700 border-emerald-100';
      case 'error': return 'bg-rose-50 text-rose-700 border-rose-100';
      case 'blocked': return 'bg-amber-50 text-amber-700 border-amber-100';
      case 'semantic_approval': return 'bg-indigo-50 text-indigo-700 border-indigo-100';
      default: return 'bg-gray-50 text-gray-700 border-gray-155';
    }
  };

  if (loading) {
    return (
      <div className="w-full flex justify-center items-center p-12 bg-white border border-gray-200 rounded-2xl shadow-sm h-64">
        <LoaderSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full p-5 bg-rose-50 border border-rose-100 rounded-2xl text-rose-700 shadow-sm flex items-center gap-3">
        <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
        <p className="text-sm font-medium">Error loading strategy history: {error}</p>
      </div>
    );
  }

  if (strategies.length === 0) {
    return (
      <div className="w-full p-12 flex flex-col items-center justify-center border border-dashed border-gray-300 rounded-2xl bg-white text-gray-400">
        <Clock className="w-12 h-12 mb-4 opacity-40" />
        <p className="text-sm font-medium">No strategies generated yet.</p>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col gap-4">
      {strategies.map((strategy) => (
        <div 
          key={strategy.id} 
          className="bg-white border border-gray-200 rounded-2xl overflow-hidden transition-all duration-200 hover:border-blue-300 hover:shadow-sm"
        >
          <div 
            className="p-5 flex flex-col sm:flex-row gap-4 items-start sm:items-center cursor-pointer select-none"
            onClick={() => setExpandedId(expandedId === strategy.id ? null : strategy.id)}
          >
            <div className="flex-shrink-0 mt-0.5 sm:mt-0">
              {getStatusIcon(strategy.status)}
            </div>
            
            <div className="flex-1 min-w-0">
              <p className="text-gray-900 text-sm font-semibold line-clamp-2 leading-relaxed">
                {strategy.prompt}
              </p>
              <div className="flex items-center gap-3 mt-2.5 text-xs font-medium">
                <span className={`px-2.5 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wider ${getStatusStyle(strategy.status)}`}>
                  {strategy.status === 'ok' ? 'Parsed' : strategy.status.replace('_', ' ')}
                </span>
                {strategy.created_at && (
                  <span className="text-gray-400 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-gray-300" />
                    {formatDistanceToNow(new Date(strategy.created_at), { addSuffix: true })}
                  </span>
                )}
              </div>
            </div>

            <div className="flex-shrink-0 self-end sm:self-auto ml-auto">
              <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${expandedId === strategy.id ? 'rotate-90 text-blue-600' : ''}`} />
            </div>
          </div>

          {expandedId === strategy.id && (
            <div className="px-6 pb-6 pt-3 border-t border-gray-150 bg-gray-50/30">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mt-3">
                {strategy.ast_json && (
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                      <FileJson className="w-4 h-4 text-gray-300" /> AST Output
                    </div>
                    <pre className="bg-slate-900 border border-slate-950 p-4 rounded-xl text-xs text-slate-100 font-mono shadow-inner overflow-auto max-h-60 custom-scrollbar">
                      {JSON.stringify(strategy.ast_json, null, 2)}
                    </pre>
                  </div>
                )}
                
                {strategy.logs && (
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                      <AlertCircle className="w-4 h-4 text-gray-300" /> Execution Logs
                    </div>
                    <pre className="bg-slate-900 border border-slate-950 p-4 rounded-xl text-xs text-slate-100 font-mono shadow-inner overflow-auto max-h-60 whitespace-pre-wrap custom-scrollbar">
                      {strategy.logs}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ))}
      
      {/* Load More Button */}
      {hasMore && !loading && (
        <div className="flex justify-center mt-4 mb-4">
          <button 
            onClick={handleLoadMore}
            disabled={loadingMore}
            className="px-6 py-2.5 border border-gray-200 text-gray-700 font-semibold rounded-xl text-sm hover:bg-gray-50 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loadingMore ? (
              <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div> Loading...</>
            ) : (
              'Load Next 10'
            )}
          </button>
        </div>
      )}
    </div>
  );
}

function LoaderSpinner() {
  return (
    <div className="flex flex-col items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-3"></div>
      <p className="text-gray-500 text-sm font-medium">Loading history list...</p>
    </div>
  );
}

```

## frontend/src/components/strategy/NewStrategyInterface.tsx
```tsx
"use client";

import React, { useState } from 'react';
import { X, Plus, Search, Calendar, DollarSign, Activity, Percent, ArrowRight } from 'lucide-react';

export default function NewStrategyInterface() {
  const [isOpen, setIsOpen] = useState(false);
  const [tradeType, setTradeType] = useState<'equity' | 'future'>('equity');
  
  // NL Space state
  const [nlInput, setNlInput] = useState('');

  // Equity state
  const [equityTicker, setEquityTicker] = useState('');
  const [equityCapital, setEquityCapital] = useState('');
  const [equityOrderType, setEquityOrderType] = useState('Market');

  // Future state
  const [futureUnderlying, setFutureUnderlying] = useState('');
  const [futureExpiry, setFutureExpiry] = useState('');
  const [futureLotSize, setFutureLotSize] = useState('');
  const [futureMargin, setFutureMargin] = useState('');

  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg shadow-lg hover:shadow-blue-500/25 transition-all duration-300"
      >
        <Plus size={20} />
        CREATE NEW STRATEGY
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-6xl h-full max-h-[90vh] bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900/50">
              <h2 className="text-xl font-bold text-white tracking-wide">New Trading Strategy</h2>
              <button 
                onClick={() => setIsOpen(false)}
                className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-full transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
              
              {/* Left Panel: NL Space */}
              <div className="flex-1 border-b lg:border-b-0 lg:border-r border-gray-800 flex flex-col bg-gray-900/30">
                <div className="px-6 py-5 flex-1 flex flex-col">
                  <label className="text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
                    <Activity size={16} className="text-blue-400" />
                    Natural Language Definition
                  </label>
                  <p className="text-xs text-gray-500 mb-4">
                    Describe your strategy in plain English. Our AI will interpret the rules and conditions.
                  </p>
                  <textarea
                    value={nlInput}
                    onChange={(e) => setNlInput(e.target.value)}
                    placeholder="e.g., Buy AAPL when the 50-day moving average crosses above the 200-day moving average, with a stop loss of 5%..."
                    className="flex-1 w-full bg-gray-950 border border-gray-800 rounded-xl p-4 text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 resize-none transition-all"
                  />
                </div>
              </div>

              {/* Right Panel: Execution Context */}
              <div className="w-full lg:w-[450px] flex flex-col bg-gray-900">
                <div className="px-6 py-5 h-full overflow-y-auto">
                  <div className="mb-6">
                    <label className="text-sm font-medium text-gray-400 mb-3 block">Asset Class</label>
                    <div className="flex p-1 bg-gray-950 rounded-lg border border-gray-800">
                      <button
                        onClick={() => setTradeType('equity')}
                        className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                          tradeType === 'equity' 
                            ? 'bg-blue-600 text-white shadow-sm' 
                            : 'text-gray-400 hover:text-gray-200 hover:bg-gray-900'
                        }`}
                      >
                        Equity Trade
                      </button>
                      <button
                        onClick={() => setTradeType('future')}
                        className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                          tradeType === 'future' 
                            ? 'bg-purple-600 text-white shadow-sm' 
                            : 'text-gray-400 hover:text-gray-200 hover:bg-gray-900'
                        }`}
                      >
                        Future Trade
                      </button>
                    </div>
                  </div>

                  {/* Conditional Rendering based on tradeType */}
                  <div className="space-y-5 animate-in fade-in slide-in-from-right-4 duration-300">
                    {tradeType === 'equity' ? (
                      <>
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-400">Stock Ticker</label>
                          <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                            <input 
                              type="text" 
                              value={equityTicker}
                              onChange={(e) => setEquityTicker(e.target.value.toUpperCase())}
                              placeholder="e.g. AAPL" 
                              className="w-full bg-gray-950 border border-gray-800 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                            />
                          </div>
                        </div>

                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-400">Capital Allocation</label>
                          <div className="relative">
                            <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                            <input 
                              type="number" 
                              value={equityCapital}
                              onChange={(e) => setEquityCapital(e.target.value)}
                              placeholder="0.00" 
                              className="w-full bg-gray-950 border border-gray-800 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                            />
                          </div>
                        </div>

                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-400">Order Type</label>
                          <div className="relative">
                            <select 
                              value={equityOrderType}
                              onChange={(e) => setEquityOrderType(e.target.value)}
                              className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none"
                            >
                              <option value="Market">Market</option>
                              <option value="Limit">Limit</option>
                              <option value="Stop">Stop Loss</option>
                              <option value="StopLimit">Stop Limit</option>
                            </select>
                            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-gray-500">
                              <svg className="h-4 w-4 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                            </div>
                          </div>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-400">Underlying Asset</label>
                          <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                            <input 
                              type="text" 
                              value={futureUnderlying}
                              onChange={(e) => setFutureUnderlying(e.target.value.toUpperCase())}
                              placeholder="e.g. NIFTY50" 
                              className="w-full bg-gray-950 border border-gray-800 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                            />
                          </div>
                        </div>

                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-400">Contract Expiry</label>
                          <div className="relative">
                            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                            <input 
                              type="date" 
                              value={futureExpiry}
                              onChange={(e) => setFutureExpiry(e.target.value)}
                              className="w-full bg-gray-950 border border-gray-800 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50 [color-scheme:dark]"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-400">Lot Size</label>
                            <input 
                              type="number" 
                              value={futureLotSize}
                              onChange={(e) => setFutureLotSize(e.target.value)}
                              placeholder="e.g. 50" 
                              className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-400">Margin Req.</label>
                            <div className="relative">
                              <Percent className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                              <input 
                                type="number" 
                                value={futureMargin}
                                onChange={(e) => setFutureMargin(e.target.value)}
                                placeholder="10.0" 
                                className="w-full bg-gray-950 border border-gray-800 rounded-lg pl-4 pr-10 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                              />
                            </div>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Footer / Action */}
                <div className="p-6 border-t border-gray-800 bg-gray-900/50">
                  <button className={`w-full py-3 px-4 rounded-lg flex items-center justify-center gap-2 font-medium text-white transition-all shadow-lg ${
                    tradeType === 'equity' 
                      ? 'bg-blue-600 hover:bg-blue-500 hover:shadow-blue-500/25' 
                      : 'bg-purple-600 hover:bg-purple-500 hover:shadow-purple-500/25'
                  }`}>
                    Review Strategy
                    <ArrowRight size={18} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

```

## frontend/src/components/strategy/BacktestConfigModal.tsx
```tsx
/**
 * Fix 4: Removed saveBacktest() — backend is single source of truth.
 *        Uses backtest_id from backend response to navigate.
 * Fix 5: Client-side validation mirroring backend rules (UX only).
 */
import React, { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useBacktestStore } from '@/store/backtestStore';
import { runBacktest } from '@/services/api';
import { Loader2 } from 'lucide-react';

const ALLOWED_TIMEFRAMES = ['1m', '2m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo'];
const ALLOWED_SIZING_MODES = ['fixed_qty', 'percent_equity'];

interface BacktestConfigModalProps {
  onClose: () => void;
  ast: any;
  canonical: any;
  defaultSymbol?: string;
  defaultTimeframe?: string;
  executionContext?: {
    universe: {
      index: string;
      exchange: string;
      asset_class: string;
    };
    timeframe: string;
    capital_per_trade: {
      amount: number;
      currency: string;
    };
    position_side: string;
    order_type: string;
    max_concurrent_positions: number;
    stock: string;
    future_contract?: {
      underlying: string;
      expiry: string;
      lot_size: number;
      margin: number;
    };
  };
  strategyId?: string | number;
}

export default function BacktestConfigModal({
  onClose,
  ast,
  canonical,
  defaultSymbol = 'RELIANCE',
  defaultTimeframe = '1d',
  executionContext,
  strategyId
}: BacktestConfigModalProps) {
  const router = useRouter();
  const setStrategyPayload = useBacktestStore((state) => state.setStrategyPayload);

  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2025-01-01');
  const [initialCapital, setInitialCapital] = useState(
    executionContext?.capital_per_trade?.amount?.toString() || '100000'
  );
  const isFutures = executionContext?.universe?.asset_class === 'futures';
  const [positionSize, setPositionSize] = useState(
    isFutures && executionContext?.future_contract?.lot_size 
      ? executionContext.future_contract.lot_size.toString() 
      : '10'
  );
  
  // Future specific fields
  const [multiplier, setMultiplier] = useState(isFutures ? '50' : ''); // Default NIFTY lot size
  const [margin, setMargin] = useState(isFutures && executionContext?.future_contract?.margin ? executionContext.future_contract.margin.toString() : '150000'); // Default approx margin per lot
  const [expiry, setExpiry] = useState(isFutures && executionContext?.future_contract?.expiry ? executionContext.future_contract.expiry : '');

  const [positionSizeType, setPositionSizeType] = useState('fixed_qty');
  const [commissionRate, setCommissionRate] = useState('0.0001');
  const [slippageBps, setSlippageBps] = useState('2.0');
  const [allowShort, setAllowShort] = useState(
    executionContext ? (executionContext.position_side === 'SHORT' || executionContext.position_side === 'BOTH') : false
  );
  const [symbol, setSymbol] = useState(
    executionContext?.stock || executionContext?.future_contract?.underlying || defaultSymbol
  );
  const [exchange, setExchange] = useState(
    executionContext?.universe?.exchange || 'NSE'
  );
  const formatTimeframe = (tf: string) => {
    if (!tf) return '';
    return tf.toLowerCase().replace('min', 'm').replace('hr', 'h');
  };

  const [timeframe, setTimeframe] = useState(
    formatTimeframe(executionContext?.timeframe || defaultTimeframe)
  );
  const [isRunning, setIsRunning] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Fix 5: Client-side validation mirroring backend rules
  const validationErrors = useMemo(() => {
    const errors: string[] = [];
    const capital = parseFloat(initialCapital);
    const posSize = parseFloat(positionSize);
    const commission = parseFloat(commissionRate);
    const slippage = parseFloat(slippageBps);

    if (!startDate || !endDate) errors.push('Start and end dates are required');
    else if (new Date(startDate) >= new Date(endDate)) errors.push('Start date must be before end date');

    if (isNaN(capital) || capital <= 0) errors.push('Initial capital must be positive');
    if (isNaN(posSize) || posSize <= 0) errors.push('Position size must be positive');
    if (isNaN(commission) || commission < 0) errors.push('Commission rate must be non-negative');
    if (isNaN(slippage) || slippage < 0) errors.push('Slippage must be non-negative');
    if (!ALLOWED_TIMEFRAMES.includes(timeframe.toLowerCase())) errors.push(`Timeframe must be one of: ${ALLOWED_TIMEFRAMES.join(', ')}`);
    if (!ALLOWED_SIZING_MODES.includes(positionSizeType)) errors.push(`Sizing mode must be one of: ${ALLOWED_SIZING_MODES.join(', ')}`);
    if (!symbol.trim()) errors.push('Symbol is required');

    return errors;
  }, [startDate, endDate, initialCapital, positionSize, commissionRate, slippageBps, timeframe, positionSizeType, symbol]);

  const isValid = validationErrors.length === 0;

  const handleRun = async () => {
    if (!isValid) {
      setValidationError(validationErrors[0]);
      return;
    }

    // Store strategy payloads for legacy reasons if any
    setStrategyPayload(ast, canonical);
    setIsRunning(true);
    setValidationError(null);

    try {
      const fullParams = {
        start_date: startDate,
        end_date: endDate,
        initial_capital: parseFloat(initialCapital),
        position_size: parseFloat(positionSize),
        position_size_type: positionSizeType,
        commission_rate: parseFloat(commissionRate),
        slippage_bps: parseFloat(slippageBps),
        allow_short: allowShort,
        symbol: symbol,
        exchange: exchange,
        position_side: executionContext?.position_side,
        timeframe: timeframe,
        strategy_id: strategyId,
        strategy_ast: ast,
        market_type: isFutures ? 'futures' : 'equity',
        multiplier: isFutures ? parseFloat(multiplier) : undefined,
        margin: isFutures ? parseFloat(margin) : undefined,
        expiry: isFutures ? expiry : undefined,
      };

      // Fix 4: Backend persists the backtest and returns backtest_id
      const result = await runBacktest(fullParams);

      // Fix 4: Navigate using the durable backend ID — no saveBacktest() call
      if (result.backtest_id) {
        router.replace(`/backtest/${result.backtest_id}`);
      }
    } catch (err: any) {
      console.error("Backtest failed", err);
      setValidationError(err.message || 'Backtest failed. Check console for details.');
      setIsRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Configure Backtest</h2>
          <button onClick={onClose} disabled={isRunning} className="text-gray-400 hover:text-gray-600 disabled:opacity-50">×</button>
        </div>

        {validationError && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
            {validationError}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1">Start Date</label>
            <input type="date" value={startDate} disabled={isRunning} onChange={e => setStartDate(e.target.value)} className="w-full border rounded p-2 text-sm disabled:opacity-50" />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1">End Date</label>
            <input type="date" value={endDate} disabled={isRunning} onChange={e => setEndDate(e.target.value)} className="w-full border rounded p-2 text-sm disabled:opacity-50" />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1">
              Initial Capital {executionContext ? <span className="text-[10px] text-gray-400 font-normal">(From Strategy)</span> : null}
            </label>
            <input
              type="number"
              value={initialCapital}
              disabled={isRunning || !!executionContext}
              onChange={e => setInitialCapital(e.target.value)}
              min={0}
              className="w-full border rounded p-2 text-sm disabled:opacity-50 disabled:bg-gray-50"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1">Position Size</label>
            <div className="flex gap-2">
              <input type="number" value={positionSize} disabled={isRunning} onChange={e => setPositionSize(e.target.value)} min={0} className="w-2/3 border rounded p-2 text-sm disabled:opacity-50" />
              <select value={positionSizeType} disabled={isRunning} onChange={e => setPositionSizeType(e.target.value)} className="w-1/3 border rounded p-2 text-sm disabled:opacity-50">
                <option value="fixed_qty">Qty</option>
                <option value="percent_equity">% Eq</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1">Commission Rate</label>
            <input type="number" value={commissionRate} disabled={isRunning} onChange={e => setCommissionRate(e.target.value)} min={0} step={0.0001} className="w-full border rounded p-2 text-sm disabled:opacity-50" />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1">Slippage (bps)</label>
            <input type="number" value={slippageBps} disabled={isRunning} onChange={e => setSlippageBps(e.target.value)} min={0} step={0.1} className="w-full border rounded p-2 text-sm disabled:opacity-50" />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1">
              {isFutures ? "Underlying Asset & Exchange" : "Symbol & Exchange"} {executionContext ? <span className="text-[10px] text-gray-400 font-normal">(From Strategy)</span> : null}
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                list="symbol-options"
                value={symbol}
                disabled={isRunning || !!executionContext}
                onChange={e => setSymbol(e.target.value)}
                className="w-2/3 border rounded p-2 text-sm disabled:opacity-50 disabled:bg-gray-50"
                placeholder={isFutures ? "e.g. RELIANCE or NIFTY 50" : "e.g. RELIANCE or AAPL"}
              />
              <datalist id="symbol-options">
                <option value="NIFTY 50" />
                <option value="NIFTY BANK" />
                <option value="RELIANCE" />
                <option value="TCS" />
                <option value="INFY" />
              </datalist>
              <select
                value={exchange}
                disabled={isRunning || !!executionContext}
                onChange={e => setExchange(e.target.value)}
                className="w-1/3 border rounded p-2 text-sm disabled:opacity-50 disabled:bg-gray-50"
              >
                <option value="NSE">NSE</option>
                <option value="BSE">BSE</option>
                <option value="NFO">NFO</option>
              </select>
            </div>
          </div>

          {isFutures && (
            <>
              <div>
                <label className="block text-xs font-bold text-purple-700 mb-1">Mode</label>
                <div className="w-full border rounded p-2 text-sm bg-purple-50 text-purple-800 font-medium border-purple-200 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></span>
                  Continuous (Auto-Spliced)
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-purple-700 mb-1">Lot Size (Multiplier)</label>
                <input
                  type="number"
                  value={multiplier}
                  disabled={isRunning || !!executionContext}
                  onChange={e => setMultiplier(e.target.value)}
                  className="w-full border rounded p-2 text-sm disabled:opacity-50 disabled:bg-gray-50 border-purple-200"
                  min={1}
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-purple-700 mb-1">Margin Per Lot</label>
                <input
                  type="number"
                  value={margin}
                  disabled={isRunning || !!executionContext}
                  onChange={e => setMargin(e.target.value)}
                  className="w-full border rounded p-2 text-sm disabled:opacity-50 disabled:bg-gray-50 border-purple-200"
                  min={0}
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1">
              Timeframe {executionContext ? <span className="text-[10px] text-gray-400 font-normal">(From Strategy)</span> : null}
            </label>
            <select
              value={timeframe}
              disabled={isRunning || !!executionContext}
              onChange={e => setTimeframe(e.target.value)}
              className="w-full border rounded p-2 text-sm disabled:opacity-50 disabled:bg-gray-50"
            >
              {ALLOWED_TIMEFRAMES.map(tf => (
                <option key={tf} value={tf}>{tf}</option>
              ))}
            </select>
          </div>
          <div className="col-span-2 flex items-center gap-2">
            <input
              type="checkbox"
              id="allowShort"
              disabled={isRunning || !!executionContext}
              checked={allowShort}
              onChange={e => setAllowShort(e.target.checked)}
              className="disabled:opacity-50"
            />
            <label htmlFor="allowShort" className="text-sm font-medium text-gray-700">
              Allow Short Selling {executionContext ? <span className="text-[10px] text-gray-400 font-normal">(From Strategy)</span> : null}
            </label>
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button onClick={onClose} disabled={isRunning} className="px-4 py-2 border rounded-lg text-sm disabled:opacity-50">Cancel</button>
          <button
            onClick={handleRun}
            disabled={isRunning || !isValid}
            className="flex items-center justify-center gap-2 px-6 py-2 bg-blue-600 text-white font-bold rounded-lg text-sm shadow-sm hover:bg-blue-700 disabled:opacity-75 min-w-[140px]"
          >
            {isRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
            {isRunning ? 'Running...' : 'Run Backtest'}
          </button>
        </div>
      </div>
    </div>
  );
}

```

## frontend/src/components/strategy/StrategySummary.tsx
```tsx
"use client";
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { BrainCircuit, Play, TrendingUp, Compass } from 'lucide-react';

interface StrategySummaryProps {
  canonicalJson?: any;
  executionContext?: any;
}

export default function StrategySummary({ canonicalJson, executionContext }: StrategySummaryProps) {
  const [data, setData] = useState<{ canonical: any; context: any }>({
    canonical: canonicalJson || null,
    context: executionContext || null
  });

  useEffect(() => {
    // If props are passed, use them
    if (canonicalJson || executionContext) {
      setData({
        canonical: canonicalJson,
        context: executionContext
      });
    }
  }, [canonicalJson, executionContext]);

  if (!data.canonical) return null;
  const { canonical, context } = data;
  const indicators = canonical?.signals?.indicators || [];

  const formatOperand = (operand: any): string => {
    if (!operand) return '';
    if (operand.type === 'market_data' || operand.type === 'market') {
      const lb = operand.lookback || 0;
      const lbStr = lb > 0 ? ` (t-${lb})` : '';
      const name = operand.data_type
        ? operand.data_type.charAt(0).toUpperCase() + operand.data_type.slice(1).toLowerCase()
        : 'Price';
      return `${name}${lbStr}`;
    }
    if (operand.type === 'indicator') {
      const ind = indicators.find((i: any) => i.id === operand.indicator_id);
      if (ind) {
        const paramParts: string[] = [];
        if (ind.params) {
          Object.entries(ind.params).forEach(([key, val]) => {
            const cleanKey = key.replace(/_/g, ' ');
            paramParts.push(`${cleanKey}: ${val}`);
          });
        }
        const paramStr = paramParts.length > 0 ? ` (${paramParts.join(', ')})` : '';
        const propStr = operand.property && operand.property !== 'value'
          ? `'s ${operand.property.replace(/_/g, ' ')}`
          : '';
        const name = ind.name
          ? ind.name.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c: string) => c.toUpperCase())
          : 'Indicator';
        return `${name}${propStr}${paramStr}`;
      }
      return operand.indicator_id || 'Indicator';
    }
    if (operand.type === 'constant' || operand.value !== undefined) {
      return String(operand.value);
    }
    return JSON.stringify(operand);
  };

  const formatOperator = (opType: string): string => {
    switch (opType) {
      case 'GREATER_THAN': return 'is greater than (>)';
      case 'LESS_THAN': return 'is less than (<)';
      case 'GREATER_THAN_EQUAL': return 'is greater than or equal to (>=)';
      case 'LESS_THAN_EQUAL': return 'is less than or equal to (<=)';
      case 'EQUAL': return 'is equal to (==)';
      case 'NOT_EQUAL': return 'is not equal to (!=)';
      case 'CROSSES_ABOVE': return 'crosses above';
      case 'CROSSES_BELOW': return 'crosses below';
      default: return opType ? opType.replace(/_/g, ' ').toLowerCase() : 'is';
    }
  };

  const formatCondition = (cond: any): string => {
    if (cond.type === 'AND' || cond.type === 'OR' || cond.operator === 'AND' || cond.operator === 'OR') {
      const children = cond.children || cond.operands || [];
      const joinStr = cond.type === 'AND' || cond.operator === 'AND' ? ' AND ' : ' OR ';
      const formattedChildren = children.map((c: any) => formatCondition(c)).filter((s: string) => s !== 'Unknown condition');
      if (formattedChildren.length === 0) return 'Unknown condition';
      if (formattedChildren.length === 1) return formattedChildren[0];
      return `(${formattedChildren.join(joinStr)})`;
    }

    const op1 = formatOperand(cond.operand_1);
    const op2 = formatOperand(cond.operand_2);
    const op = formatOperator(cond.type || cond.operator);
    if (!op1 && !op2) return 'Unknown condition';
    return `${op1} ${op} ${op2}`;
  };

  // Generate Entry and Exit Conditions list
  const entryConditions: string[] = [];
  const exitConditions: string[] = [];
  
  if (canonical?.operation && Array.isArray(canonical.operation)) {
    canonical.operation.forEach((op: any, index: number) => {
      const prefix = canonical.operation.length > 1 ? `[Leg ${index + 1}] ` : '';
      
      const entries = op.entry || [];
      entries.forEach((cond: any) => {
        entryConditions.push(prefix + formatCondition(cond));
      });
      
      const exits = op.exit || [];
      exits.forEach((cond: any) => {
        exitConditions.push(prefix + formatCondition(cond));
      });
    });
  }

  // Generate Risk & Context details list
  const riskList: string[] = [];
  const risk = canonical?.risk;
  if (risk) {
    if (risk.stop_loss && risk.stop_loss.value !== null && risk.stop_loss.value !== undefined) {
      const val = risk.stop_loss.value;
      const type = risk.stop_loss.type || 'percentage';
      riskList.push(`Stop Loss: ${val}${type === 'percentage' ? '%' : ` ${type}`}`);
    }
    if (risk.take_profit && risk.take_profit.value !== null && risk.take_profit.value !== undefined) {
      const val = risk.take_profit.value;
      const type = risk.take_profit.type || 'percentage';
      riskList.push(`Take Profit: ${val}${type === 'percentage' ? '%' : ` ${type}`}`);
    }
    if (risk.risk_reward && risk.risk_reward.value !== null && risk.risk_reward.value !== undefined) {
      riskList.push(`Risk Reward Ratio: 1:${risk.risk_reward.value}`);
    } else if (risk.risk_reward && risk.risk_reward.ratio !== null && risk.risk_reward.ratio !== undefined) {
      riskList.push(`Risk Reward Ratio: 1:${risk.risk_reward.ratio}`);
    }
    if (risk.trailing_stop && risk.trailing_stop.value !== null && risk.trailing_stop.value !== undefined) {
      const val = risk.trailing_stop.value;
      const type = risk.trailing_stop.type || 'percentage';
      riskList.push(`Trailing Stop: ${val}${type === 'percentage' ? '%' : ` ${type}`}`);
    }
  }

  if (context) {
    if (context.position_side) {
      riskList.push(`Position Side: ${context.position_side}`);
    }
    if (context.max_concurrent_positions !== undefined) {
      riskList.push(`Max Concurrent Positions: ${context.max_concurrent_positions}`);
    }
    if (context.capital_per_trade) {
      const cap = context.capital_per_trade;
      if (cap.amount !== undefined) {
        riskList.push(`Capital per Trade: ${cap.amount.toLocaleString()} ${cap.currency || 'INR'}`);
      }
    }
    if (context.timeframe) {
      riskList.push(`Timeframe: ${context.timeframe}`);
    }
    if (context.universe) {
      const uni = context.universe;
      riskList.push(`Universe: ${uni.index || 'NIFTY_50'} (${uni.exchange || 'NSE'})`);
    }
  }

  return (
    <section id="what-i-understood" className="w-full">
      <div className="bg-white border border-gray-150 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center">
              <BrainCircuit className="text-xl" size={20} />
            </div>
            <h2 className="text-lg font-bold text-gray-900">Summary</h2>
          </div>
          <Link id="edit-strategy-btn" href="/strategy" className="text-xs font-bold text-blue-600 hover:underline">
            Edit Strategy
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
          <div className="space-y-4">
            <div>
              <div className="flex items-center gap-1.5 mb-3">
                <TrendingUp className="text-emerald-500 shrink-0" size={16} />
                <h3 className="text-xs font-bold text-blue-600 uppercase tracking-widest">Entry Conditions</h3>
              </div>
              {entryConditions.length > 0 ? (
                <ul className="space-y-2 text-gray-700 font-medium">
                  {entryConditions.map((cond, idx) => (
                    <li key={idx} className="flex items-start gap-2 leading-relaxed">
                      <span className="text-blue-400 shrink-0 mt-1">•</span>
                      <span>{cond}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-gray-400 italic">No entry conditions specified.</p>
              )}
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <div className="flex items-center gap-1.5 mb-3">
                <Play className="text-rose-500 rotate-90 shrink-0" size={16} />
                <h3 className="text-xs font-bold text-blue-600 uppercase tracking-widest">Exit Conditions</h3>
              </div>
              {exitConditions.length > 0 ? (
                <ul className="space-y-2 text-gray-700 font-medium">
                  {exitConditions.map((cond, idx) => (
                    <li key={idx} className="flex items-start gap-2 leading-relaxed">
                      <span className="text-blue-400 shrink-0 mt-1">•</span>
                      <span>{cond}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-gray-400 italic">No exit conditions specified.</p>
              )}
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <div className="flex items-center gap-1.5 mb-3">
                <Compass className="text-blue-500 shrink-0" size={16} />
                <h3 className="text-xs font-bold text-blue-600 uppercase tracking-widest">Risk & Execution</h3>
              </div>
              {riskList.length > 0 ? (
                <ul className="space-y-2 text-gray-700 font-medium">
                  {riskList.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2 leading-relaxed">
                      <span className="text-blue-400 shrink-0 mt-1">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-gray-400 italic">No custom risk parameters defined.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

```

## frontend/src/components/strategy/ValidationStatus.tsx
```tsx
import React from 'react';
import { Check } from 'lucide-react';

export default function ValidationStatus() {
  return (
    <section id="validation-status" className="grid grid-cols-1 md:grid-cols-3 gap-4 pb-12">
      <div className="validation-card">
        <div className="w-10 h-10 bg-emerald-500 text-white rounded-2xl flex items-center justify-center shadow-md">
          <Check className="text-lg" size={20} />
        </div>
        <p className="text-sm font-bold text-emerald-800">No blockers found</p>
      </div>
      <div className="validation-card">
        <div className="w-10 h-10 bg-emerald-500 text-white rounded-2xl flex items-center justify-center shadow-md">
          <Check className="text-lg" size={20} />
        </div>
        <p className="text-sm font-bold text-emerald-800">Strategy can be compiled</p>
      </div>
      <div className="validation-card">
        <div className="w-10 h-10 bg-emerald-500 text-white rounded-2xl flex items-center justify-center shadow-md">
          <Check className="text-lg" size={20} />
        </div>
        <p className="text-sm font-bold text-emerald-800">Ready for backtesting</p>
      </div>
    </section>
  );
}

```

