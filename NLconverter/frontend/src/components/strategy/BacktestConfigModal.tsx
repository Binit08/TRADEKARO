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
  { value: 'HINDZINC', label: 'H हिंदुस्तान Zinc Ltd' },
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
    position_side: string;
    order_type?: string;
    stock?: string;
    stocks?: string[];
    future_contract?: {
      underlying: string;
      expiry: string;
      lot_size: number;
      margin: number;
      multiplier?: number;
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
  const [initialCapital, setInitialCapital] = useState('100000');
  const isFutures = executionContext?.universe?.asset_class === 'futures';
  const [positionSize, setPositionSize] = useState(
    isFutures && executionContext?.future_contract?.lot_size 
      ? executionContext.future_contract.lot_size.toString() 
      : '10'
  );
  // Future specific fields
  const [multiplier, setMultiplier] = useState(
    isFutures && executionContext?.future_contract?.multiplier
      ? executionContext.future_contract.multiplier.toString()
      : (isFutures ? '50' : '')
  );
  const [margin, setMargin] = useState(
    isFutures && executionContext?.future_contract?.margin 
      ? executionContext.future_contract.margin.toString() 
      : (isFutures ? '150000' : '')
  );
  const [expiry] = useState(
    isFutures && executionContext?.future_contract?.expiry 
      ? executionContext.future_contract.expiry 
      : ''
  );

  const [positionSizeType, setPositionSizeType] = useState('fixed_qty');
  const [commissionRate, setCommissionRate] = useState('0.0001');
  const [slippageBps, setSlippageBps] = useState('2.0');
  const [allowShort, setAllowShort] = useState(
    executionContext ? (executionContext.position_side === 'SHORT' || executionContext.position_side === 'BOTH') : false
  );
  const [symbol, setSymbol] = useState(
    executionContext?.stocks?.join(', ') || executionContext?.stock || executionContext?.future_contract?.underlying || defaultSymbol
  );
  const [exchange, setExchange] = useState(
    executionContext?.universe?.exchange || 'NSE'
  );
  const [brokerName, setBrokerName] = useState('kite');
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
        symbol: symbol.split(',').map(s => s.trim()).filter(Boolean)[0] || '',
        symbols: symbol.split(',').map(s => s.trim()).filter(Boolean),
        exchange: exchange,
        position_side: executionContext?.position_side,
        timeframe: timeframe,
        strategy_id: strategyId,
        strategy_ast: ast,
        market_type: isFutures ? 'futures' : 'equity',
        broker_name: brokerName,
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
      console.warn("Backtest failed:", err.message);
      setValidationError(err.message || 'Backtest failed. Check console for details.');
      setIsRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-surface rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-foreground">Configure Backtest</h2>
          <button onClick={onClose} disabled={isRunning} className="text-muted hover:text-muted disabled:opacity-50">×</button>
        </div>

        {validationError && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
            {validationError}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="block text-xs font-bold text-gray-700 mb-1">Execution Broker</label>
            <select value={brokerName} disabled={isRunning} onChange={e => setBrokerName(e.target.value)} className="w-full border rounded p-2 text-sm disabled:opacity-50 font-semibold bg-background border-blue-200">
              <option value="kite">Zerodha Kite (Default)</option>
              <option value="shoonya">Finvasia Shoonya</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1">Start Date</label>
            <input type="date" value={startDate} disabled={isRunning} onChange={e => setStartDate(e.target.value)} className="w-full border rounded p-2 text-sm disabled:opacity-50" />
          </div>
          <div>
            <label className="block text-xs font-bold text-foreground mb-1">End Date</label>
            <input type="date" value={endDate} disabled={isRunning} onChange={e => setEndDate(e.target.value)} className="w-full border rounded p-2 text-sm disabled:opacity-50" />
          </div>
          <div>
            <label className="block text-xs font-bold text-foreground mb-1">
              Initial Capital {executionContext ? <span className="text-[10px] text-muted font-normal">(From Strategy)</span> : null}
            </label>
            <input
              type="number"
              value={initialCapital}
              disabled={isRunning || !!executionContext}
              onChange={e => setInitialCapital(e.target.value)}
              min={0}
              className="w-full border rounded p-2 text-sm disabled:opacity-50 disabled:bg-background"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-foreground mb-1">Position Size</label>
            <div className="flex gap-2">
              <input type="number" value={positionSize} disabled={isRunning} onChange={e => setPositionSize(e.target.value)} min={0} className="w-2/3 border rounded p-2 text-sm disabled:opacity-50" />
              <select value={positionSizeType} disabled={isRunning} onChange={e => setPositionSizeType(e.target.value)} className="w-1/3 border rounded p-2 text-sm disabled:opacity-50">
                <option value="fixed_qty">Qty</option>
                <option value="percent_equity">% Eq</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-bold text-foreground mb-1">Commission Rate</label>
            <input type="number" value={commissionRate} disabled={isRunning} onChange={e => setCommissionRate(e.target.value)} min={0} step={0.0001} className="w-full border rounded p-2 text-sm disabled:opacity-50" />
          </div>
          <div>
            <label className="block text-xs font-bold text-foreground mb-1">Slippage (bps)</label>
            <input type="number" value={slippageBps} disabled={isRunning} onChange={e => setSlippageBps(e.target.value)} min={0} step={0.1} className="w-full border rounded p-2 text-sm disabled:opacity-50" />
          </div>
          <div>
            <label className="block text-xs font-bold text-foreground mb-1">
              {isFutures ? "Underlying Asset(s) & Exchange" : "Symbols (comma-separated) & Exchange"} {executionContext ? <span className="text-[10px] text-muted font-normal">(From Strategy)</span> : null}
            </label>
            <div className="flex gap-2">
              <input
                list="config-stock-options"
                value={symbol}
                disabled={isRunning}
                onChange={e => setSymbol(e.target.value)}
                className="w-2/3 border rounded p-2 text-sm disabled:opacity-50 disabled:bg-background bg-surface"
                placeholder="e.g. RELIANCE, TCS"
              />
              <datalist id="config-stock-options">
                {STOCK_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </datalist>
              <select
                value={exchange}
                disabled={isRunning || !!executionContext}
                onChange={e => setExchange(e.target.value)}
                className="w-1/3 border rounded p-2 text-sm disabled:opacity-50 disabled:bg-background"
              >
                <option value="NSE">NSE</option>
                <option value="BSE">BSE</option>
                <option value="NFO">NFO</option>
                <option value="MCX">MCX</option>
                <option value="CRYPTO">CRYPTO (Binance Test)</option>
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
                  className="w-full border rounded p-2 text-sm disabled:opacity-50 disabled:bg-background border-purple-200"
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
                  className="w-full border rounded p-2 text-sm disabled:opacity-50 disabled:bg-background border-purple-200"
                  min={0}
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-bold text-foreground mb-1">
              Timeframe {executionContext ? <span className="text-[10px] text-muted font-normal">(From Strategy)</span> : null}
            </label>
            <select
              value={timeframe}
              disabled={isRunning || !!executionContext}
              onChange={e => setTimeframe(e.target.value)}
              className="w-full border rounded p-2 text-sm disabled:opacity-50 disabled:bg-background"
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
            <label htmlFor="allowShort" className="text-sm font-medium text-foreground">
              Allow Short Selling {executionContext ? <span className="text-[10px] text-muted font-normal">(From Strategy)</span> : null}
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
