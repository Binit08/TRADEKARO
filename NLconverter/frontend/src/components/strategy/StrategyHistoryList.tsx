"use client";

import React, { useEffect, useState } from 'react';
import { getStrategyHistory } from '@/services/api';
import { Clock, CheckCircle, XCircle, AlertCircle, HelpCircle, ChevronRight, FileJson } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import BacktestConfigModal from './BacktestConfigModal';
import PaperTradeConfigModal from './PaperTradeConfigModal';
import Loader from '@/components/ui/Loader';

interface StrategyRecord {
  id: number;
  name?: string;
  tag?: string;
  description?: string;
  prompt: string;
  status: string;
  created_at: string;
  canonical_json: any;
  ast_json: any;
  logs: string;
}

export function StrategyHistoryList({ loadAll = false }: { loadAll?: boolean }) {
  const [strategies, setStrategies] = useState<StrategyRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [backtestStrategyId, setBacktestStrategyId] = useState<number | null>(null);
  const [paperTradeStrategyId, setPaperTradeStrategyId] = useState<number | null>(null);

  const fetchHistory = async (currentOffset = 0, isLoadMore = false) => {
    try {
      if (isLoadMore) setLoadingMore(true);
      else setLoading(true);
      
      const pageSize = loadAll ? 100 : 10;
      let data = await getStrategyHistory(pageSize, currentOffset);
      if (data.status === 'ok') {
        if (loadAll && !isLoadMore) {
          const allStrategies = [...data.strategies];
          let nextOffset = currentOffset + pageSize;

          while (data.has_more) {
            data = await getStrategyHistory(pageSize, nextOffset);
            if (data.status !== 'ok') break;
            allStrategies.push(...data.strategies);
            nextOffset += pageSize;
          }

          setStrategies(allStrategies);
          setHasMore(false);
          setOffset(currentOffset);
          return;
        }

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
      default: return <Clock className="w-5 h-5 text-muted" />;
    }
  };

  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'ok': return 'bg-emerald-50 text-emerald-700 border-emerald-100';
      case 'error': return 'bg-rose-50 text-rose-700 border-rose-100';
      case 'blocked': return 'bg-amber-50 text-amber-700 border-amber-100';
      case 'semantic_approval': return 'bg-indigo-50 text-indigo-700 border-indigo-100';
      default: return 'bg-background text-foreground border-gray-155';
    }
  };

  if (loading) {
    return (
      <div className="w-full flex justify-center items-center p-12 bg-surface border border-border rounded-2xl shadow-sm h-64">
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
      <div className="w-full p-12 flex flex-col items-center justify-center border border-dashed border-border rounded-2xl bg-surface text-muted">
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
          className="bg-surface border border-border shadow-sm rounded-2xl overflow-hidden transition-all duration-200 hover:border-blue-300 hover:shadow-md"
        >
          <div 
            className="p-5 flex flex-col sm:flex-row gap-4 items-start sm:items-center cursor-pointer select-none"
            onClick={() => setExpandedId(expandedId === strategy.id ? null : strategy.id)}
          >
            <div className="flex-shrink-0 mt-0.5 sm:mt-0">
              {getStatusIcon(strategy.status)}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <p className="text-foreground text-base font-bold truncate">
                  {strategy.name || "Untitled Strategy"}
                </p>
                {strategy.tag && (
                  <span className="px-2 py-0.5 rounded border border-border bg-background text-[10px] font-bold text-muted uppercase tracking-wider">
                    {strategy.tag}
                  </span>
                )}
              </div>
              <p className="text-muted text-sm line-clamp-2">
                {strategy.description || strategy.prompt}
              </p>
              <div className="flex items-center gap-3 mt-2.5 text-xs font-medium">
                <span className={`px-2.5 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wider ${getStatusStyle(strategy.status)}`}>
                  {strategy.status === 'ok' ? 'Ready' : strategy.status === 'semantic_approval' ? 'Verified' : strategy.status.replace('_', ' ')}
                </span>
                {strategy.created_at && (
                  <span className="text-muted flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-gray-300" />
                    {formatDistanceToNow(new Date(strategy.created_at), { addSuffix: true })}
                  </span>
                )}
              </div>
            </div>

            <div className="flex-shrink-0 self-end sm:self-auto ml-auto">
              <ChevronRight className={`w-5 h-5 text-muted transition-transform duration-200 ${expandedId === strategy.id ? 'rotate-90 text-blue-600' : ''}`} />
            </div>
          </div>

          {expandedId === strategy.id && (
            <div className="px-6 pb-6 pt-3 border-t border-border bg-background/30">
              <div className="mb-4">
                <div className="flex items-center gap-2 text-[10px] font-bold text-muted uppercase tracking-wider mb-2">
                  <CheckCircle className="w-4 h-4 text-gray-300" /> Entry & Exit Conditions
                </div>
                <div className="bg-surface border border-border p-4 rounded-xl text-sm text-foreground shadow-sm whitespace-pre-wrap leading-relaxed">
                  {strategy.prompt}
                </div>
              </div>
              <div className="flex items-center justify-end gap-3 mb-4">
                <button
                  onClick={() => setPaperTradeStrategyId(strategy.id)}
                  disabled={strategy.status !== 'ok' || !strategy.ast_json}
                  className="px-5 py-2 bg-emerald-600 text-white rounded-lg font-semibold text-sm hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Paper Trade
                </button>
                <button
                  onClick={() => setBacktestStrategyId(strategy.id)}
                  disabled={strategy.status !== 'ok' || !strategy.ast_json}
                  className="px-5 py-2 bg-blue-600 text-white rounded-lg font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Run Backtest
                </button>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mt-3">
                {strategy.ast_json && (
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-muted uppercase tracking-wider">
                      <FileJson className="w-4 h-4 text-gray-300" /> AST Output
                    </div>
                    <pre className="bg-slate-900 border border-slate-950 p-4 rounded-xl text-xs text-slate-100 font-mono shadow-inner overflow-auto max-h-60 custom-scrollbar">
                      {JSON.stringify(strategy.ast_json, null, 2)}
                    </pre>
                  </div>
                )}
                
                {strategy.logs && (
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-muted uppercase tracking-wider">
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
            className="px-6 py-2.5 border border-border text-foreground font-semibold rounded-xl text-sm hover:bg-background transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loadingMore ? (
              <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div> Loading...</>
            ) : (
              'Load Next 10'
            )}
          </button>
        </div>
      )}

      {backtestStrategyId && (
        <BacktestConfigModal
          ast={strategies.find(s => s.id === backtestStrategyId)?.ast_json}
          canonical={strategies.find(s => s.id === backtestStrategyId)?.canonical_json}
          onClose={() => setBacktestStrategyId(null)}
          strategyId={backtestStrategyId}
        />
      )}

      {paperTradeStrategyId && (
        <PaperTradeConfigModal
          ast={strategies.find(s => s.id === paperTradeStrategyId)?.ast_json}
          canonical={strategies.find(s => s.id === paperTradeStrategyId)?.canonical_json}
          onClose={() => setPaperTradeStrategyId(null)}
          strategyId={paperTradeStrategyId}
        />
      )}
    </div>
  );
}

function LoaderSpinner() {
  return (
    <div className="flex flex-col items-center justify-center">
      <Loader />
      <p className="text-muted text-sm font-medium mt-4">Loading history list...</p>
    </div>
  );
}
