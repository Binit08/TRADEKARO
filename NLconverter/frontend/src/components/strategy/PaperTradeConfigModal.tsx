import React, { useState } from 'react';
import { X, Play, Loader2, AlertCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { startPaperTrade } from '@/services/api';

interface PaperTradeConfigModalProps {
  ast: any;
  canonical: any;
  onClose: () => void;
  strategyId: number;
}

export default function PaperTradeConfigModal({
  ast,
  canonical,
  onClose,
  strategyId
}: PaperTradeConfigModalProps) {
  const router = useRouter();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [symbol, setSymbol] = useState(canonical?.universe?.index || 'RELIANCE');
  const [timeframe, setTimeframe] = useState(canonical?.timeframe || '1m');
  const [exchange, setExchange] = useState(canonical?.universe?.exchange || 'NSE');
  const [initialCash, setInitialCash] = useState(100000);
  const [positionSize, setPositionSize] = useState(1.0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await startPaperTrade({
        symbols: [symbol],
        timeframe: timeframe,
        exchange: exchange,
        strategy_ast: canonical || ast,
        initial_cash: initialCash,
        position_size: positionSize
      });

      if (response.session_id) {
        onClose();
        router.push(`/paper-trade?sessionId=${response.session_id}`);
      } else {
        throw new Error('Failed to start paper trade (no session ID returned)');
      }
    } catch (err: any) {
      console.error('Paper trade error:', err);
      setError(err.message || 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div className="bg-surface rounded-2xl shadow-xl w-full max-w-md overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-background">
          <div>
            <h2 className="text-lg font-bold text-foreground">Start Paper Trade</h2>
            <p className="text-xs text-muted mt-0.5">Configure live simulated execution</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-muted hover:text-muted hover:bg-slate-200 rounded-full transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[70vh]">
          {error && (
            <div className="mb-6 p-4 bg-rose-50 border border-rose-100 rounded-xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
              <p className="text-sm text-rose-700">{error}</p>
            </div>
          )}

          <form id="paper-trade-form" onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-bold text-foreground mb-1.5">Symbol</label>
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full px-4 py-2.5 bg-background border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-surface transition-all uppercase"
                placeholder="e.g. RELIANCE"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-bold text-foreground mb-1.5">Exchange</label>
              <select
                value={exchange}
                onChange={(e) => setExchange(e.target.value)}
                className="w-full px-4 py-2.5 bg-background border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-surface transition-all"
              >
                <option value="NSE">NSE</option>
                <option value="BSE">BSE</option>
                <option value="NFO">NFO</option>
                <option value="MCX">MCX</option>
                <option value="CRYPTO">CRYPTO (Binance Test)</option>
              </select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-bold text-foreground mb-1.5">Initial Capital</label>
                <input
                  type="number"
                  value={initialCash}
                  onChange={(e) => setInitialCash(Number(e.target.value))}
                  className="w-full px-4 py-2.5 bg-background border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-surface transition-all"
                  min="1"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-foreground mb-1.5">Quantity (Qty)</label>
                <input
                  type="number"
                  value={positionSize}
                  onChange={(e) => setPositionSize(Number(e.target.value))}
                  className="w-full px-4 py-2.5 bg-background border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-surface transition-all"
                  min="0.01"
                  step="0.01"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-foreground mb-1.5">Timeframe</label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full px-4 py-2.5 bg-background border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-surface transition-all"
              >
                <option value="1m">1 Minute</option>
                <option value="5m">5 Minutes</option>
                <option value="15m">15 Minutes</option>
                <option value="1h">1 Hour</option>
                <option value="1d">1 Day</option>
              </select>
              <p className="text-xs text-muted mt-1.5">
                The candlestick frequency for evaluating signals.
              </p>
            </div>
          </form>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border bg-background flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 text-sm font-bold text-muted hover:text-foreground transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            form="paper-trade-form"
            disabled={loading}
            className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold rounded-xl shadow-sm hover:shadow transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Starting...</>
            ) : (
              <><Play className="w-4 h-4" /> Start Live Execution</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
