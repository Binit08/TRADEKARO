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
  entry_reason?: string;
  exit_reason?: string;
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

  // Calculate Cumulative PnL and sort descending by trade number
  let cumPnl = 0;
  const processedTrades = [...filteredTrades]
    .sort((a, b) => new Date(a.entry_time).getTime() - new Date(b.entry_time).getTime())
    .map((trade, idx) => {
      const pnl = trade.pnl ?? trade.unrealized_pnl ?? 0;
      cumPnl += pnl;
      const notional = trade.qty * trade.entry_price;
      const returnPct = notional !== 0 ? (pnl / notional) * 100 : 0;
      
      return {
        ...trade,
        tradeNumber: idx + 1,
        cumPnl,
        notional,
        returnPct,
      };
    })
    .reverse();

  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 3 }).format(val) + ' INR';
    
  const formatCurrencyK = (val: number) => 
    new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val / 1000) + 'K INR';

  const formatPct = (val: number) => 
    (val > 0 ? '+' : '') + new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val) + '%';

  const formatTime = (timeStr?: string) => {
    if (!timeStr) return '-';
    
    // Check if it is a numeric timestamp
    let numVal;
    if (!isNaN(Number(timeStr))) {
        numVal = Number(timeStr);
        // Convert seconds to milliseconds if needed
        if (numVal < 1e11) numVal *= 1000;
        const date = new Date(numVal);
        return new Intl.DateTimeFormat('en-US', { 
          month: 'short', day: 'numeric', year: 'numeric', 
          hour: '2-digit', minute: '2-digit', hour12: false 
        }).format(date);
    }
    
    let safeStr = timeStr.replace(' ', 'T');
    const hasTime = safeStr.includes('T');
    const hasTimezone = safeStr.endsWith('Z') || (hasTime && safeStr.indexOf('+', safeStr.indexOf('T')) !== -1) || (hasTime && safeStr.indexOf('-', safeStr.indexOf('T')) !== -1);
    
    // If backend provides naive UTC strings, append Z to force Date to parse as UTC
    if (hasTime && !hasTimezone) {
      safeStr += 'Z';
    }
    
    const date = new Date(safeStr);
    if (isNaN(date.getTime())) return timeStr;
    return new Intl.DateTimeFormat('en-US', { 
      month: 'short', day: 'numeric', year: 'numeric', 
      hour: '2-digit', minute: '2-digit', hour12: false 
    }).format(date);
  };

  return (
    <div className="bg-surface border border-border rounded-xl shadow-sm overflow-hidden flex flex-col h-full text-foreground font-sans">
      <div className="px-5 py-4 border-b border-border flex items-center justify-between bg-surface">
        <h2 className="text-lg font-semibold text-foreground tracking-wide">List of trades</h2>
        <div className="flex gap-3">
          <select 
            value={filterSide} 
            onChange={(e) => setFilterSide(e.target.value)}
            className="text-xs uppercase tracking-wider border border-border rounded px-2 py-1 bg-surface text-foreground outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="ALL">ALL TYPES</option>
            <option value="LONG">LONG</option>
            <option value="SHORT">SHORT</option>
          </select>
        </div>
      </div>
      
      <div className="overflow-auto flex-1 bg-background">
        {processedTrades.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted uppercase tracking-widest">
            No trades match filters
          </div>
        ) : (
          <table className="w-full text-left text-[13px] border-collapse relative">
            <thead className="sticky top-0 z-10 bg-surface/90 backdrop-blur border-b border-border">
              <tr className="text-muted font-normal">
                <th className="py-4 px-6 font-medium whitespace-nowrap">Trade number &darr;</th>
                <th className="py-4 px-4 font-medium">Type</th>
                <th className="py-4 px-4 font-medium">Date and time</th>
                <th className="py-4 px-4 font-medium">Signal</th>
                <th className="py-4 px-4 font-medium text-right">Price</th>
                <th className="py-4 px-6 font-medium text-right">Size</th>
                <th className="py-4 px-6 font-medium text-right">Net PnL</th>
                <th className="py-4 px-6 font-medium text-right">Cumulative PnL</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60 bg-surface">
              {processedTrades.map((trade) => {
                const isLong = trade.side === 'BUY' || trade.side === 'LONG';
                const pnl = trade.pnl ?? trade.unrealized_pnl ?? 0;
                const isWin = pnl >= 0;
                const pnlColor = isWin ? 'text-emerald-600' : 'text-rose-600';

                return (
                  <tr key={trade.tradeNumber} className="hover:bg-background transition-colors">
                    <td className="py-4 px-6 align-middle border-r border-border">
                      <span className="text-foreground font-medium mr-2">{trade.tradeNumber}</span>
                      <span className="text-blue-600 text-sm font-medium">{isLong ? 'long' : 'short'}</span>
                    </td>
                    
                    <td className="py-4 px-4 align-middle text-muted">
                      <div className="flex flex-col gap-4">
                        <span>Exit</span>
                        <span>Entry</span>
                      </div>
                    </td>

                    <td className="py-4 px-4 align-middle text-foreground whitespace-nowrap">
                      <div className="flex flex-col gap-4">
                        <span>{trade.exit_price ? formatTime(trade.exit_time) : '(Open)'}</span>
                        <span>{formatTime(trade.entry_time)}</span>
                      </div>
                    </td>

                    <td className="py-4 px-4 align-middle text-foreground">
                      <div className="flex flex-col gap-4">
                        <span>{trade.exit_reason || (trade.exit_price ? 'Exit' : '-')}</span>
                        <span>{trade.entry_reason || (isLong ? 'Long' : 'Short')}</span>
                      </div>
                    </td>

                    <td className="py-4 px-4 align-middle text-right text-foreground whitespace-nowrap border-r border-border">
                      <div className="flex flex-col gap-4">
                        <span className="font-medium">{trade.exit_price ? formatCurrency(trade.exit_price) : '-'}</span>
                        <span className="font-medium">{formatCurrency(trade.entry_price)}</span>
                      </div>
                    </td>

                    <td className="py-4 px-6 align-middle text-right">
                      <div className="flex flex-col">
                        <span className="text-foreground font-medium">{trade.qty.toFixed(0)}</span>
                        <span className="text-muted text-xs mt-1">{formatCurrencyK(trade.notional)}</span>
                      </div>
                    </td>

                    <td className="py-4 px-6 align-middle text-right">
                      <div className="flex flex-col">
                        <span className={`${pnlColor} font-medium`}>
                          {isWin ? '+' : ''}{formatCurrency(pnl)}
                        </span>
                        <span className={`${pnlColor} text-xs mt-1 font-medium`}>
                          {formatPct(trade.returnPct)}
                        </span>
                      </div>
                    </td>

                    <td className="py-4 px-6 align-middle text-right">
                      <div className="flex flex-col">
                        <span className="text-foreground font-medium">
                          {formatCurrency(trade.cumPnl)}
                        </span>
                      </div>
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

