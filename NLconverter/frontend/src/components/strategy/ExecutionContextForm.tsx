"use client";
import React, { useState, useEffect, useMemo } from 'react';
import { Plus, Info, ChevronDown } from 'lucide-react';
import AddInstrumentsModal from './AddInstrumentsModal';


export const STOCK_OPTIONS = [
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

interface ExecutionContextFormProps {
  context: {
    universe: {
      index: string;
      exchange: string;
      asset_class: string;
    };
    timeframe: string;
    position_side: string;
    stocks: string[];
    future_contract?: {
      underlying: string;
      expiry: string;
      lot_size: number;
      margin: number;
    };
  };
  setContext: React.Dispatch<React.SetStateAction<any>>;
  strategyType: 'equity' | 'future';
}

export default function ExecutionContextForm({ context, setContext, strategyType }: ExecutionContextFormProps) {
  const [isInstrumentModalOpen, setIsInstrumentModalOpen] = useState(false);
  const [futuresData, setFuturesData] = useState<any[]>([]);
  const [isLoadingFutures, setIsLoadingFutures] = useState(false);
  const isEquity = strategyType === 'equity';

  useEffect(() => {
    if (!isEquity && futuresData.length === 0) {
      setIsLoadingFutures(true);
      fetch('/api/proxy/futures')
        .then(res => res.json())
        .then(data => {
          if (data.status === 'ok') {
            setFuturesData(data.data);
          }
        })
        .catch(err => console.error("Error fetching futures:", err))
        .finally(() => setIsLoadingFutures(false));
    }
  }, [isEquity, futuresData.length]);

  const indexFutures = useMemo(() => futuresData.filter(f => f.type === 'INDEX'), [futuresData]);
  const stockFutures = useMemo(() => futuresData.filter(f => f.type === 'STOCK'), [futuresData]);
  const selectedFuture = useMemo(() => futuresData.find(f => f.name === context.future_contract?.underlying), [futuresData, context.future_contract?.underlying]);

  const handleUnderlyingChange = (underlying: string) => {
    const future = futuresData.find(f => f.name === underlying);
    if (future && future.expiries.length > 0) {
      setContext({
        ...context,
        future_contract: {
          ...(context.future_contract || {}),
          underlying,
          expiry: future.expiries[0].date,
          lot_size: future.expiries[0].lot_size,
        }
      });
    } else {
      setContext({
        ...context,
        future_contract: {
          ...(context.future_contract || {}),
          underlying,
          expiry: '',
          lot_size: 0,
        }
      });
    }
  };
  
  const handleExpiryChange = (expiryDate: string) => {
    const exp = selectedFuture?.expiries.find((e: any) => e.date === expiryDate);
    setContext({
      ...context,
      future_contract: {
        ...(context.future_contract || {}),
        expiry: expiryDate,
        lot_size: exp ? exp.lot_size : (context.future_contract?.lot_size || 0),
      }
    });
  };

  return (
    <aside className="lg:col-span-4 flex flex-col gap-6 relative z-10 text-foreground h-full">
      <div className="p-5 lg:p-6 rounded-2xl bg-surface border border-border shadow-sm flex-1 flex flex-col min-h-0 overflow-y-auto">
        <div className="flex items-center justify-between mb-6 shrink-0">
          <h2 className="text-xl font-bold font-display tracking-tight">Chart Settings</h2>
        </div>

        <div className="space-y-6">
          {/* Selectors */}
          <div className="flex flex-wrap gap-4">
            <button className="flex-1 px-4 py-2.5 rounded-xl border border-border bg-surface shadow-sm text-sm font-bold flex items-center justify-between transition-soft hover:bg-background">
              Candlestick
              <ChevronDown size={16} />
            </button>
            <div className="flex-1 relative border border-border bg-surface shadow-sm rounded-xl transition-soft hover:bg-background">
              <select
                value={context.timeframe}
                onChange={(e) => setContext({ ...context, timeframe: e.target.value })}
                className="w-full h-full px-4 py-2.5 appearance-none bg-transparent text-sm font-bold focus:outline-none focus:ring-0"
              >
                <option value="" disabled>Timeframe</option>
                <option value="1m">1 Minute</option>
                <option value="3m">3 Minutes</option>
                <option value="5m">5 Minutes</option>
                <option value="15m">15 Minutes</option>
                <option value="30m">30 Minutes</option>
                <option value="1h">1 Hour</option>
                <option value="1d">1 Day</option>
              </select>
              <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none">
                <ChevronDown size={16} />
              </div>
            </div>
          </div>

          {isEquity ? (
            /* EQUITY FIELDS */
            <>
              {/* Instruments */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-muted mb-4">Instruments</h3>
                
                {context.stocks && context.stocks.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {context.stocks.slice(0, 5).map((symbol: string, idx: number) => (
                      <div 
                        key={`${symbol}-${idx}`} 
                        className="px-3 py-1.5 rounded-lg border border-border bg-background text-indigo-600 text-xs font-bold"
                        title={symbol}
                      >
                        {symbol}
                      </div>
                    ))}
                    {context.stocks.length > 5 && (
                      <div className="px-3 py-1.5 rounded-lg border border-border bg-background text-muted text-xs font-bold">
                        +{context.stocks.length - 5}
                      </div>
                    )}
                  </div>
                )}
                
                <button
                  type="button"
                  onClick={() => setIsInstrumentModalOpen(true)}
                  className="w-full py-2.5 rounded-xl border border-dashed border-indigo-300 bg-indigo-50 flex items-center justify-center gap-2 text-indigo-600 font-bold transition-soft hover:bg-indigo-100"
                >
                  <Plus size={18} />
                  Add Instruments
                </button>
              </div>

              {/* Position Side */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-muted mb-4">Position Side</h3>
                <div className="flex p-1 rounded-xl bg-surface border border-border gap-1">
                  <button 
                    onClick={() => setContext({ ...context, position_side: 'LONG' })}
                    className={`flex-1 py-2 rounded-lg text-sm font-bold transition-soft ${
                      context.position_side === 'LONG' 
                        ? 'bg-surface shadow-sm border border-border text-foreground' 
                        : 'text-muted hover:text-foreground hover:bg-background border border-transparent'
                    }`}
                  >
                    LONG
                  </button>
                  <button 
                    onClick={() => setContext({ ...context, position_side: 'SHORT' })}
                    className={`flex-1 py-2 rounded-lg text-sm font-bold transition-soft ${
                      context.position_side === 'SHORT' 
                        ? 'bg-surface shadow-sm border border-border text-foreground' 
                        : 'text-muted hover:text-foreground hover:bg-background border border-transparent'
                    }`}
                  >
                    SHORT
                  </button>
                </div>
              </div>
            </>
          ) : (
            /* FUTURES FIELDS */
            <>
              {/* Underlying Asset */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-muted mb-4">Underlying Asset</h3>
                <div className="relative border border-border bg-surface shadow-sm rounded-xl transition-soft hover:bg-background">
                  <select
                    value={context.future_contract?.underlying || ''}
                    onChange={(e) => handleUnderlyingChange(e.target.value)}
                    className="w-full h-full px-4 py-2.5 appearance-none bg-transparent text-sm font-bold focus:outline-none focus:ring-0"
                  >
                    <option value="" disabled>{isLoadingFutures ? 'Loading...' : 'Select Underlying'}</option>
                    <optgroup label="Index Futures">
                      {indexFutures.map((option) => (
                        <option key={option.name} value={option.name}>{option.name}</option>
                      ))}
                    </optgroup>
                    <optgroup label="Stock Futures">
                      {stockFutures.map((option) => (
                        <option key={option.name} value={option.name}>{option.name}</option>
                      ))}
                    </optgroup>
                  </select>
                  <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none">
                    <ChevronDown size={16} />
                  </div>
                </div>
              </div>

              {/* Expiry & Lots */}
              <div className="flex gap-4">
                <div className="flex-1">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-muted mb-4">Expiry</h3>
                  <div className="relative border border-border bg-surface shadow-sm rounded-xl transition-soft hover:bg-background">
                    <select
                      value={context.future_contract?.expiry || ''}
                      onChange={(e) => handleExpiryChange(e.target.value)}
                      disabled={!selectedFuture}
                      className="w-full h-full px-4 py-2.5 appearance-none bg-transparent text-sm font-bold focus:outline-none focus:ring-0 disabled:opacity-50"
                    >
                      <option value="" disabled>Select Expiry</option>
                      {selectedFuture?.expiries.map((exp: any) => (
                        <option key={exp.date} value={exp.date}>{exp.date}</option>
                      ))}
                    </select>
                    <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none">
                      <ChevronDown size={16} />
                    </div>
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-muted mb-4">Lots</h3>
                  <div className="relative border border-border bg-surface shadow-sm rounded-xl transition-soft hover:bg-background">
                    <input
                      type="number"
                      value={context.future_contract?.lot_size || ''}
                      onChange={(e) => setContext({ 
                        ...context, 
                        future_contract: { ...(context.future_contract || {}), lot_size: parseInt(e.target.value, 10) || 0 }
                      })}
                      className="w-full h-full px-4 py-2.5 appearance-none bg-transparent text-sm font-bold focus:outline-none focus:ring-0"
                    />
                  </div>
                </div>
              </div>

              {/* Position Side */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-muted mb-4">Position Side</h3>
                <div className="flex p-1 rounded-xl bg-surface border border-border gap-1">
                  <button 
                    onClick={() => setContext({ ...context, position_side: 'LONG' })}
                    className={`flex-1 py-2 rounded-lg text-sm font-bold transition-soft ${
                      context.position_side === 'LONG' 
                        ? 'bg-surface shadow-sm border border-border text-indigo-600' 
                        : 'text-muted hover:text-foreground hover:bg-background border border-transparent'
                    }`}
                  >
                    LONG
                  </button>
                  <button 
                    onClick={() => setContext({ ...context, position_side: 'SHORT' })}
                    className={`flex-1 py-2 rounded-lg text-sm font-bold transition-soft ${
                      context.position_side === 'SHORT' 
                        ? 'bg-surface shadow-sm border border-border text-indigo-600' 
                        : 'text-muted hover:text-foreground hover:bg-background border border-transparent'
                    }`}
                  >
                    SHORT
                  </button>
                  <button 
                    onClick={() => setContext({ ...context, position_side: 'BOTH' })}
                    className={`flex-1 py-2 rounded-lg text-sm font-bold transition-soft ${
                      context.position_side === 'BOTH' 
                        ? 'bg-surface shadow-sm border border-border text-indigo-600' 
                        : 'text-muted hover:text-foreground hover:bg-background border border-transparent'
                    }`}
                  >
                    BOTH
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      <AddInstrumentsModal
        isOpen={isInstrumentModalOpen}
        onClose={() => setIsInstrumentModalOpen(false)}
        selectedStocks={context.stocks || []}
        onSave={(selected) => setContext({ ...context, stocks: selected })}
      />
    </aside>
  );
}
