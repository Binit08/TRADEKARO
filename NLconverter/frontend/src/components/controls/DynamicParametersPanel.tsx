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

const STOCK_OPTIONS = [
  { value: 'RELIANCE', label: 'Reliance Industries Ltd' },
  { value: 'TCS', label: 'Tata Consultancy Services Ltd' },
  { value: 'HDFCBANK', label: 'HDFC Bank Ltd' },
  { value: 'INFY', label: 'Infosys Ltd' },
  { value: 'HDFC', label: 'HDFC Ltd' },
  { value: 'ICICIBANK', label: 'ICICI Bank Ltd' },
  { value: 'KOTAKBANK', label: 'Kotak Mahindra Bank Ltd' },
  { value: 'HINDUNILVR', label: 'Hindustan Unilever Ltd' },
  { value: 'BHARTIARTL', label: 'Bharti Airtel Ltd' },
  { value: 'SBIN', label: 'State Bank of India' },
  { value: 'AXISBANK', label: 'Axis Bank Ltd' },
  { value: 'LT', label: 'Larsen & Toubro Ltd' },
  { value: 'ITC', label: 'ITC Ltd' },
  { value: 'BAJFINANCE', label: 'Bajaj Finance Ltd' },
  { value: 'MARUTI', label: 'Maruti Suzuki India Ltd' },
  { value: 'TITAN', label: 'Titan Company Ltd' },
  { value: 'BAJAJFINSV', label: 'Bajaj Finserv Ltd' },
  { value: 'SUNPHARMA', label: 'Sun Pharmaceutical Industries Ltd' },
  { value: 'JSWSTEEL', label: 'JSW Steel Ltd' },
  { value: 'ONGC', label: 'Oil and Natural Gas Corporation Ltd' },
  { value: 'ULTRACEMCO', label: 'UltraTech Cement Ltd' },
  { value: 'NTPC', label: 'NTPC Ltd' },
  { value: 'POWERGRID', label: 'Power Grid Corporation of India Ltd' },
  { value: 'TATASTEEL', label: 'Tata Steel Ltd' },
  { value: 'NESTLEIND', label: 'Nestle India Ltd' },
  { value: 'HCLTECH', label: 'HCL Technologies Ltd' },
  { value: 'ADANIENT', label: 'Adani Enterprises Ltd' },
  { value: 'ASIANPAINT', label: 'Asian Paints Ltd' },
  { value: 'WIPRO', label: 'Wipro Ltd' },
  { value: 'EICHERMOT', label: 'Eicher Motors Ltd' },
  { value: 'HINDALCO', label: 'Hindalco Industries Ltd' },
  { value: 'COALINDIA', label: 'Coal India Ltd' },
  { value: 'BRITANNIA', label: 'Britannia Industries Ltd' },
  { value: 'DIVISLAB', label: "Divi's Laboratories Ltd" },
  { value: 'HINDZINC', label: 'Hindustan Zinc Ltd' },
  { value: 'BPCL', label: 'Bharat Petroleum Corporation Ltd' },
  { value: 'HINDPETRO', label: 'Hindustan Petroleum Corporation Ltd' },
  { value: 'TATACONSUM', label: 'Tata Consumer Products Ltd' },
  { value: 'GRASIM', label: 'Grasim Industries Ltd' },
  { value: 'DRREDDY', label: 'Dr. Reddy’s Laboratories Ltd' },
  { value: 'TECHM', label: 'Tech Mahindra Ltd' },
  { value: 'SBILIFE', label: 'SBI Life Insurance Company Ltd' },
  { value: 'SHREECEM', label: 'Shree Cement Ltd' },
  { value: 'TATACHEM', label: 'Tata Chemicals Ltd' },
  { value: 'M&M', label: 'Mahindra & Mahindra Ltd' },
  { value: 'GAIL', label: 'GAIL (India) Ltd' },
  { value: 'INDUSINDBK', label: 'IndusInd Bank Ltd' },
];

interface DynamicParametersPanelProps {
  initialParams?: any;
  strategyAst?: any;
}

export default function DynamicParametersPanel({ initialParams, strategyAst }: DynamicParametersPanelProps) {
  const router = useRouter();

  const [localParams, setLocalParams] = useState({
    symbol: initialParams?.symbols?.join(', ') || initialParams?.symbol || 'RELIANCE',
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
      const parsedSymbols = localParams.symbol ? localParams.symbol.split(',').map((s: string) => s.trim()).filter(Boolean) : [];
      const fullParams = {
        ...localParams,
        symbol: parsedSymbols[0] || '',
        symbols: parsedSymbols,
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
    <div className="bg-surface border border-border rounded-2xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-foreground">Dynamic Parameters</h3>
      </div>

      {validationError && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-2 text-xs text-red-700">
          {validationError}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-[10px] font-bold text-muted uppercase tracking-wider mb-1">Symbols & Exchange</label>
          <div className="flex gap-2">
            <input
              list="dynamic-stock-options"
              value={localParams.symbol || ''}
              onChange={(e) => handleUpdate('symbol', e.target.value)}
              className="w-1/2 lg:w-2/3 text-xs border rounded p-2 bg-surface"
              placeholder="e.g. RELIANCE, TCS"
            />
            <datalist id="dynamic-stock-options">
              {STOCK_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </datalist>
            <select
              value={localParams.exchange || 'NSE'}
              onChange={(e) => handleUpdate('exchange', e.target.value)}
              className="w-1/2 lg:w-1/3 text-xs border rounded p-2 bg-surface"
            >
              <option value="NSE">NSE</option>
              <option value="BSE">BSE</option>
              <option value="NFO">NFO</option>
              <option value="MCX">MCX</option>
              <option value="CRYPTO">CRYPTO (Binance Test)</option>
            </select>
          </div>
        </div>
        <div>
          <label className="block text-[10px] font-bold text-muted uppercase tracking-wider mb-1">Timeframe</label>
          <select
            value={localParams.timeframe || '1d'}
            onChange={(e) => handleUpdate('timeframe', e.target.value)}
            className="w-full text-xs border rounded p-2 bg-surface"
          >
            {ALLOWED_TIMEFRAMES.map(tf => (
              <option key={tf} value={tf}>{tf}</option>
            ))}
          </select>
        </div>
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-muted uppercase tracking-widest">Initial Cash</label>
          <input
            type="number"
            value={localParams.initial_cash}
            onChange={(e) => handleUpdate('initial_cash', parseFloat(e.target.value))}
            className="w-full px-3 py-2 bg-surface border border-border rounded-md text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all font-mono"
          />
        </div>
        <div>
          <label className="block text-[10px] font-bold text-muted uppercase tracking-wider mb-1">Position Size</label>
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
              className="w-1/3 text-xs border rounded p-2 bg-surface"
            >
              <option value="fixed_qty">Qty</option>
              <option value="percent_equity">% Eq</option>
            </select>
          </div>
        </div>
        <div>
          <label className="block text-[10px] font-bold text-muted uppercase tracking-wider mb-1">Start Date</label>
          <input
            type="date"
            value={localParams.start_date || ''}
            onChange={(e) => handleUpdate('start_date', e.target.value)}
            className="w-full text-xs border rounded p-2 bg-surface"
          />
        </div>
        <div>
          <label className="block text-[10px] font-bold text-muted uppercase tracking-wider mb-1">End Date</label>
          <input
            type="date"
            value={localParams.end_date || ''}
            onChange={(e) => handleUpdate('end_date', e.target.value)}
            className="w-full text-xs border rounded p-2 bg-surface"
          />
        </div>
        <div>
          <label className="block text-[10px] font-bold text-muted uppercase tracking-wider mb-1">Commission</label>
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
          <label className="block text-[10px] font-bold text-muted uppercase tracking-wider mb-1">Slippage (bps)</label>
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
          <label htmlFor="allowShortDynamic" className="text-xs font-bold text-foreground">Allow Shorting</label>
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
