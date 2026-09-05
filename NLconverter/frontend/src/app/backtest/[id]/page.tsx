"use client";
import React, { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Loader2, AlertTriangle, Filter } from 'lucide-react';
import { getBacktest } from '@/services/api';
import OverviewCards from '@/components/metrics/OverviewCards';
import EquityCurveChart from '@/components/charts/EquityCurveChart';
import DrawdownChart from '@/components/charts/DrawdownChart';
import CandlestickChart from '@/components/charts/CandlestickChart';
import TradeListTable from '@/components/trades/TradeListTable';
import DynamicParametersPanel from '@/components/controls/DynamicParametersPanel';
import InnerHeader from '@/components/layout/InnerHeader';
import Loader from '@/components/ui/Loader';

export default function BacktestResultPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const resolvedParams = use(params);
  const id = resolvedParams.id;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<any | null>(null);
  const [backtestData, setBacktestData] = useState<any | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('ALL');

  useEffect(() => {
    if (!id || id === 'latest') {
      setError("Invalid backtest ID. Please generate a strategy first.");
      setLoading(false);
      return;
    }

    const fetchBacktest = async () => {
      try {
        setLoading(true);
        const data = await getBacktest(id);
        setBacktestData(data);
        if (data && data.ohlc_data && !Array.isArray(data.ohlc_data)) {
          const keys = Object.keys(data.ohlc_data);
          if (keys.length === 1) {
            setSelectedSymbol(keys[0]);
          } else if (keys.length > 1) {
            setSelectedSymbol('ALL');
          }
        }
      } catch (err: any) {
        console.error(err);
        setError(err.message || "Failed to load backtest result");
      } finally {
        setLoading(false);
      }
    };

    fetchBacktest();
  }, [id]);

  const handleBack = () => {
    router.push('/strategy/review');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <InnerHeader />
        <main className="flex-1 max-w-7xl mx-auto w-full p-6 flex flex-col items-center justify-center">
          <Loader />
          <p className="text-muted font-medium mt-4">Loading backtest report...</p>
        </main>
      </div>
    );
  }

  // Filter Trades based on selectedSymbol
  const allTrades = backtestData?.trades || [];
  const filteredTrades = selectedSymbol === 'ALL' 
    ? allTrades 
    : allTrades.filter((t: any) => t.symbol === selectedSymbol);

  // Process data for charts
  let equityData: any[] = [];
  let drawdownData: any[] = [];
  let ohlcData: any[] = [];
  let displayMetrics: any = null;
  
  if (backtestData) {
    // 1. OHLC Data for Candlestick
    const chartSymbol = selectedSymbol === 'ALL' 
      ? (backtestData.ohlc_data && !Array.isArray(backtestData.ohlc_data) ? Object.keys(backtestData.ohlc_data)[0] : null)
      : selectedSymbol;
      
    if (Array.isArray(backtestData.ohlc_data)) {
      ohlcData = backtestData.ohlc_data;
    } else if (backtestData.ohlc_data && chartSymbol) {
      ohlcData = backtestData.ohlc_data[chartSymbol] || [];
    }

    // 2. Metrics, Equity & Drawdown Curves
    if (selectedSymbol === 'ALL') {
      displayMetrics = backtestData.metrics || {};
      
      equityData = (backtestData.equity_curve || []).map((p: any) => ({
        time: p.time,
        value: p.value,
        benchmark: p.benchmark_value
      }));
      
      drawdownData = (backtestData.drawdown_curve || []).map((p: any) => {
        let dd = p.drawdown ?? p.drawdownPct ?? p.drawdown_pct ?? 0;
        if (dd > 0) dd = -dd; 
        if (dd > -1 && dd < 0) dd = dd * 100; // Convert to percentage if it's a decimal
        return {
          time: typeof p.time === 'string' ? p.time.split('T')[0] : p.time,
          drawdown: parseFloat(dd.toFixed(2))
        };
      });
    } else {
      const symResult = backtestData.metrics?.symbol_results?.[selectedSymbol];
      if (symResult) {
        displayMetrics = symResult.metrics || {};
        
        equityData = (symResult.equity_curve || []).map((p: any) => ({
          time: typeof p.time === 'string' ? p.time.split('T')[0] : p.time,
          value: p.value || p.equity
        }));
        
        drawdownData = (symResult.equity_curve || []).map((p: any) => {
          let dd = p.drawdown ?? p.drawdownPct ?? p.drawdown_pct ?? 0;
          if (dd > 0) dd = -dd; 
          return {
            time: typeof p.time === 'string' ? p.time.split('T')[0] : p.time,
            drawdown: parseFloat(dd.toFixed(2))
          };
        });
      }
    }
  }

  const hasMultipleSymbols = backtestData?.ohlc_data && !Array.isArray(backtestData.ohlc_data) && Object.keys(backtestData.ohlc_data).length > 1;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <InnerHeader />
      <main className="flex-1 max-w-7xl mx-auto w-full p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={handleBack} className="p-2 hover:bg-slate-200 rounded-full transition-colors text-muted">
              <ArrowLeft className="text-xl" size={20} />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-foreground">Backtest Results</h1>
              <p className="text-sm text-muted">Performance and execution analysis.</p>
            </div>
          </div>
          <button 
            onClick={async () => {
              try {
                const response = await fetch('/api/proxy/paper_trade/start', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    symbols: selectedSymbol === 'ALL' ? (backtestData.symbol ? backtestData.symbol.split(', ').map((s: string) => s.trim()) : ['RELIANCE']) : [selectedSymbol],
                    timeframe: backtestData.timeframe || '1m',
                    broker_name: backtestData.broker_name || 'kite',
                    strategy_ast: backtestData.strategy_json || backtestData.strategy_ast,
                    exchange: backtestData.exchange || 'NSE'
                  })
                });
                
                const data = await response.json();
                if (!response.ok) {
                  alert(`Failed to start paper trading: ${data.detail || 'Unknown error'}`);
                  return;
                }
                
                if (data.session_id) {
                  router.push(`/paper-trade?sessionId=${data.session_id}`);
                }
              } catch (e) {
                console.error(e);
                alert("Network error starting paper trade.");
              }
            }}
            className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold rounded-xl shadow-sm transition-colors"
          >
            <div className="w-2 h-2 bg-surface rounded-full animate-pulse"></div>
            Start Paper Trading
          </button>
        </div>

        {error && (
          <div className="rounded-xl bg-rose-50 border border-rose-200 p-5 text-sm text-rose-700 shadow-sm flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 shrink-0 text-rose-600 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-bold text-rose-800 mb-1">Error</h4>
              <p className="text-rose-700">{error}</p>
            </div>
          </div>
        )}

        {backtestData && (
          <div className="space-y-6">
            {hasMultipleSymbols && (
              <div className="bg-surface p-4 rounded-2xl border border-border shadow-sm flex items-center gap-4 overflow-x-auto">
                <div className="flex items-center gap-2 text-muted shrink-0">
                  <Filter size={16} />
                  <span className="text-sm font-bold uppercase tracking-wider">Results View:</span>
                </div>
                <button
                  onClick={() => setSelectedSymbol('ALL')}
                  className={`px-5 py-2 rounded-xl text-sm font-bold transition-all shrink-0 ${
                    selectedSymbol === 'ALL' 
                      ? 'bg-slate-900 text-white shadow-md' 
                      : 'bg-muted/10 text-muted hover:bg-slate-200'
                  }`}
                >
                  Aggregate Portfolio
                </button>
                <div className="w-px h-6 bg-slate-200 shrink-0"></div>
                {Object.keys(backtestData.ohlc_data).map(sym => (
                  <button
                    key={sym}
                    onClick={() => setSelectedSymbol(sym)}
                    className={`px-5 py-2 rounded-xl text-sm font-bold transition-all shrink-0 ${
                      selectedSymbol === sym 
                        ? 'bg-blue-600 text-white shadow-md' 
                        : 'bg-surface border border-border text-muted hover:bg-slate-50'
                    }`}
                  >
                    {sym}
                  </button>
                ))}
              </div>
            )}

            <OverviewCards metrics={displayMetrics} />
            
            <DynamicParametersPanel 
              initialParams={{
                symbol: backtestData.symbol,
                timeframe: backtestData.timeframe,
                initial_capital: backtestData.initial_capital || backtestData.initial_cash,
                position_size: backtestData.position_size,
                position_size_type: backtestData.position_size_type || 'fixed_qty',
                commission_rate: backtestData.commission_rate ?? 0.0001,
                slippage_bps: backtestData.slippage_bps ?? 2.0,
                allow_short: backtestData.allow_short || false,
                exchange: backtestData.exchange || 'NSE',
                start_date: backtestData.start_date,
                end_date: backtestData.end_date,
              }}
              strategyAst={backtestData.strategy_json || backtestData.strategy_ast}
            />

            <div className="bg-surface border border-border rounded-2xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-foreground">Price Action & Trade Executions</h3>
                {selectedSymbol === 'ALL' && hasMultipleSymbols && (
                  <div className="text-xs font-medium text-muted bg-muted/10 px-3 py-1 rounded-lg">
                    Showing chart for {Object.keys(backtestData.ohlc_data)[0]}
                  </div>
                )}
              </div>
              {ohlcData.length > 0 ? (
                <CandlestickChart 
                  ohlcData={ohlcData} 
                  trades={filteredTrades} 
                  timeframe={backtestData.timeframe || '1d'} 
                />
              ) : (
                <div className="h-[350px] flex items-center justify-center text-muted text-sm">No price data available</div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-surface border border-border rounded-2xl p-5 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-foreground">Equity Curve</h3>
                {equityData.length > 0 ? (
                  <EquityCurveChart data={equityData} />
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-muted text-sm">No data available</div>
                )}
              </div>
              
              <div className="bg-surface border border-border rounded-2xl p-5 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-foreground">Drawdown</h3>
                {drawdownData.length > 0 ? (
                  <DrawdownChart data={drawdownData} />
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-muted text-sm">No data available</div>
                )}
              </div>
            </div>

            <div className="h-[400px]">
              <TradeListTable trades={filteredTrades} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
