"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getBacktests, BacktestListItem } from '@/services/api';
import { 
  History, 
  TrendingUp, 
  TrendingDown, 
  Percent, 
  Hash, 
  Calendar, 
  ChevronRight,
  Loader2,
  AlertTriangle,
  Play
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import Loader from '@/components/ui/Loader';

interface Backtest extends BacktestListItem {
  trades?: any[] | null;
  metadata?: any | null;
}

export function BacktestHistoryList() {
  const router = useRouter();
  const [backtests, setBacktests] = useState<Backtest[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [totalCount, setTotalCount] = useState(0);

  const fetchBacktestsList = async (currentOffset = 0, isLoadMore = false) => {
    try {
      if (isLoadMore) setLoadingMore(true);
      else setLoading(true);
      
      const pageSize = 100;
      let response = await getBacktests(pageSize, currentOffset);
      const allBacktests = [...(response.data || [])];

      let nextOffset = currentOffset + pageSize;
      while (response.has_more) {
        response = await getBacktests(pageSize, nextOffset);
        allBacktests.push(...(response.data || []));
        nextOffset += pageSize;
      }
      
      if (isLoadMore) {
        setBacktests(prev => [...prev, ...allBacktests]);
      } else {
        setBacktests(allBacktests);
      }
      setHasMore(false);
      setTotalCount(response.total_count);
      setOffset(currentOffset);
    } catch (err: any) {
      console.error("Failed to load backtests:", err);
      setError(err.message || "Failed to load backtest history");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    fetchBacktestsList();
  }, []);

  const handleLoadMore = () => {
    fetchBacktestsList(offset + 10, true);
  };

  const totalRuns = totalCount || backtests.length;
  const totalNetProfit = backtests.reduce((acc, b) => acc + (b.net_profit || 0), 0);
  const avgReturn = totalRuns > 0 
    ? backtests.reduce((acc, b) => acc + (b.total_return || 0), 0) / totalRuns 
    : 0;
  const avgWinRate = totalRuns > 0
    ? backtests.reduce((acc, b) => acc + (b.win_rate || 0), 0) / totalRuns
    : 0;
  const totalTradesCount = backtests.reduce((acc, b) => {
    return acc + (b.total_trades || 0);
  }, 0);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(value);
  };

  const handleRowClick = (id: string) => {
    router.push(`/backtest/${id}`);
  };

  return (
    <div className="w-full space-y-5">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1
            className="text-2xl font-bold text-foreground"
            style={{ fontFamily: '"Space Grotesk", sans-serif' }}
          >
            Backtest History
          </h1>
          <p className="mt-1 text-sm text-muted">
            View performance summaries and execution metrics for all your run strategies.
          </p>
        </div>
        <button 
          onClick={() => router.push('/strategy')}
          className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2.5 rounded-xl text-sm transition-all shadow-sm shadow-blue-500/10 self-start md:self-auto"
        >
          <Play size={15} />
          Run New Backtest
        </button>
      </div>

      {loading ? (
        <div className="h-96 flex flex-col items-center justify-center bg-surface border border-border rounded-2xl shadow-sm">
          <Loader />
          <p className="text-muted font-medium text-sm mt-4">Loading backtest history...</p>
        </div>
      ) : error ? (
        <div className="rounded-2xl bg-rose-50 border border-rose-100 p-6 shadow-sm flex items-start gap-4">
          <AlertTriangle className="w-6 h-6 text-rose-600 mt-0.5 shrink-0" />
          <div>
            <h4 className="font-bold text-rose-800 text-sm">Error Loading History</h4>
            <p className="text-rose-700 text-sm mt-1">{error}</p>
            <button 
              onClick={() => window.location.reload()}
              className="mt-3 text-xs font-bold text-rose-800 underline hover:text-rose-900"
            >
              Try Again
            </button>
          </div>
        </div>
      ) : backtests.length === 0 ? (
        <div className="h-96 flex flex-col items-center justify-center bg-surface border border-border border-dashed rounded-2xl p-8 text-center">
          <div className="p-4 bg-background text-muted rounded-2xl mb-4">
            <History className="w-10 h-10" />
          </div>
          <h3 className="text-base font-bold text-foreground">No Backtests Run Yet</h3>
          <p className="text-sm text-muted max-w-sm mt-2 mb-6">
            You haven't run any strategy backtests. Navigate to the strategies builder to test your strategy logic against historical data.
          </p>
          <button 
            onClick={() => router.push('/strategy')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-5 py-2.5 rounded-xl text-sm transition-all shadow-sm shadow-blue-500/10"
          >
            Go to Strategy Builder
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-surface border border-border rounded-2xl p-5 shadow-sm hover:shadow-md transition-all">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted uppercase tracking-wider">Total Backtests</span>
                <div className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
                  <History size={16} />
                </div>
              </div>
              <div className="text-2xl font-black text-foreground mt-2">{totalRuns}</div>
              <div className="text-[10px] text-muted mt-1">Completed strategy runs</div>
            </div>

            <div className="bg-surface border border-border rounded-2xl p-5 shadow-sm hover:shadow-md transition-all">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted uppercase tracking-wider">Cumulative P&L</span>
                <div className={`p-1.5 rounded-lg ${totalNetProfit >= 0 ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
                  {totalNetProfit >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                </div>
              </div>
              <div className={`text-2xl font-black mt-2 ${totalNetProfit >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                {totalNetProfit >= 0 ? '+' : ''}{formatCurrency(totalNetProfit)}
              </div>
              <div className="text-[10px] text-muted mt-1">Across all historical runs</div>
            </div>

            <div className="bg-surface border border-border rounded-2xl p-5 shadow-sm hover:shadow-md transition-all">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted uppercase tracking-wider">Avg. Return %</span>
                <div className={`p-1.5 rounded-lg ${avgReturn >= 0 ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
                  <Percent size={16} />
                </div>
              </div>
              <div className={`text-2xl font-black mt-2 ${avgReturn >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                {avgReturn >= 0 ? '+' : ''}{avgReturn.toFixed(2)}%
              </div>
              <div className="text-[10px] text-muted mt-1">Average profit per backtest</div>
            </div>

            <div className="bg-surface border border-border rounded-2xl p-5 shadow-sm hover:shadow-md transition-all">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted uppercase tracking-wider">Overall Win Rate</span>
                <div className="p-1.5 bg-amber-50 text-amber-600 rounded-lg">
                  <Hash size={16} />
                </div>
              </div>
              <div className="text-2xl font-black text-foreground mt-2">{avgWinRate.toFixed(1)}%</div>
              <div className="text-[10px] text-muted mt-1">From {totalTradesCount} executed trades</div>
            </div>
          </div>

          <div className="bg-surface border border-border rounded-2xl shadow-sm overflow-hidden">
            <div className="px-6 py-5 border-b border-border flex items-center justify-between bg-background/50">
              <h2 className="text-base font-bold text-foreground">Historical Strategy Runs</h2>
              <span className="text-xs font-semibold bg-gray-150 text-muted px-2.5 py-1 rounded-full border border-border">
                {totalRuns} runs stored
              </span>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-background/50 text-[10px] font-bold text-muted uppercase tracking-wider border-b border-border">
                    <th className="px-6 py-4">Symbol / Timeframe</th>
                    <th className="px-6 py-4">Date Range</th>
                    <th className="px-6 py-4">Initial Capital</th>
                    <th className="px-6 py-4">Trades</th>
                    <th className="px-6 py-4">Win Rate</th>
                    <th className="px-6 py-4">Net Profit</th>
                    <th className="px-6 py-4">Return %</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 font-medium text-foreground text-sm">
                  {backtests.map((backtest) => {
                    const trades = backtest.total_trades || backtest.trades || backtest.metadata?.total_trades || 0;
                    const tradesCount = Array.isArray(trades) ? trades.length : Number(trades);
                    
                    const dateRangeStr = backtest.start_date && backtest.end_date
                      ? `${backtest.start_date} → ${backtest.end_date}`
                      : 'Custom Range';
                    
                    return (
                      <tr 
                        key={backtest.id} 
                        onClick={() => handleRowClick(String(backtest.id))}
                        className="hover:bg-background/80 cursor-pointer transition-colors group"
                      >
                        <td className="px-6 py-4.5">
                          <div className="flex flex-col">
                            <span className="font-semibold text-foreground group-hover:text-blue-600 transition-colors">
                              {backtest.symbol.replace('.NS', '').replace('.BO', '')}
                            </span>
                            <span className="text-xs text-muted font-mono flex items-center gap-1 mt-0.5">
                              {backtest.timeframe}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4.5 text-muted text-xs">
                          <div className="flex items-center gap-1.5">
                            <Calendar size={13} className="text-muted" />
                            <span>{dateRangeStr}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4.5 font-mono text-muted text-xs">
                          {formatCurrency(backtest.initial_cash)}
                        </td>
                        <td className="px-6 py-4.5 font-mono text-muted">
                          {tradesCount}
                        </td>
                        <td className="px-6 py-4.5 font-bold text-foreground">
                          {backtest.win_rate != null ? `${backtest.win_rate.toFixed(1)}%` : 'N/A'}
                        </td>
                        <td className={`px-6 py-4.5 font-mono font-black ${
                          (backtest.net_profit || 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'
                        }`}>
                          {(backtest.net_profit || 0) >= 0 ? '+' : ''}
                          {formatCurrency(backtest.net_profit || 0)}
                        </td>
                        <td className="px-6 py-4.5">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold ${
                            (backtest.total_return || 0) >= 0 
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                              : 'bg-rose-50 text-rose-700 border border-rose-100'
                          }`}>
                            {(backtest.total_return || 0) >= 0 ? '+' : ''}
                            {(backtest.total_return || 0).toFixed(2)}%
                          </span>
                        </td>
                        <td className="px-6 py-4.5 text-right">
                          <div className="flex items-center justify-end gap-1.5 text-muted group-hover:text-blue-600 transition-colors">
                            <span className="text-xs font-semibold opacity-0 group-hover:opacity-100 transition-opacity">View Report</span>
                            <ChevronRight size={16} />
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="px-6 py-4 border-t border-border bg-background/30 flex justify-between items-center text-xs text-muted">
              <span>Click on any row to open the detailed interactive backtest report.</span>
              <span>Last updated {backtests.length > 0 ? formatDistanceToNow(new Date(backtests[0].created_at), { addSuffix: true }) : 'just now'}</span>
            </div>
          </div>
        </>
      )}
      
      {hasMore && !loading && (
        <div className="flex justify-center mt-6 mb-8">
          <button 
            onClick={handleLoadMore}
            disabled={loadingMore}
            className="px-6 py-2.5 border border-border text-foreground font-semibold rounded-xl text-sm hover:bg-background transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loadingMore ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Loading...</>
            ) : (
              'Load Next 10'
            )}
          </button>
        </div>
      )}
    </div>
  );
}
