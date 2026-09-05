import React, { useState, useMemo, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Search, X, Minus, Check, Loader2 } from 'lucide-react';

interface AddInstrumentsModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedStocks: string[];
  onSave: (selected: string[]) => void;
}

const INDICES = ['NIFTY50', 'NIFTY100', 'NIFTY200', 'NIFTY500', 'BANKNIFTY'];

export default function AddInstrumentsModal({ isOpen, onClose, selectedStocks, onSave }: AddInstrumentsModalProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState<string | null>('NIFTY50');
  const [currentSelection, setCurrentSelection] = useState<string[]>(selectedStocks);
  const [mounted, setMounted] = useState(false);
  const [instrumentsList, setInstrumentsList] = useState<{value: string, label: string}[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setMounted(true);
    fetchInstruments();
  }, []);

  const fetchInstruments = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/proxy/instruments');
      const data = await res.json();
      if (data.status === 'ok') {
        setInstrumentsList(data.instruments);
      }
    } catch (e) {
      console.error("Failed to fetch instruments:", e);
    } finally {
      setLoading(false);
    }
  };

  // Sync state when modal opens
  useEffect(() => {
    if (isOpen) {
      setCurrentSelection(selectedStocks);
      setSearchQuery('');
    }
  }, [isOpen, selectedStocks]);

const INDEX_CONSTITUENTS: Record<string, string[]> = {
  'NIFTY50': [
    'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'INFY', 'ITC', 'SBIN', 'BHARTIARTL', 
    'HINDUNILVR', 'KOTAKBANK', 'LT', 'AXISBANK', 'BAJFINANCE', 'MARUTI', 'ASIANPAINT', 
    'HCLTECH', 'TITAN', 'SUNPHARMA', 'TATASTEEL', 'ULTRACEMCO', 'NTPC', 'M&M', 'POWERGRID', 
    'NESTLEIND', 'BAJAJFINSV', 'TECHM', 'JSWSTEEL', 'GRASIM', 'HINDALCO', 'WIPRO', 'ONGC', 
    'ADANIENT', 'ADANIPORTS', 'COALINDIA', 'SBILIFE', 'HDFCLIFE', 'DRREDDY', 'EICHERMOT', 
    'APOLLOHOSP', 'DIVISLAB', 'CIPLA', 'TATAMOTORS', 'BRITANNIA', 'BAJAJ-AUTO', 'TATACONSUM', 
    'HEROMOTOCO', 'UPL', 'BPCL', 'INDUSINDBK'
  ],
  'BANKNIFTY': [
    'HDFCBANK', 'ICICIBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK', 'INDUSINDBK', 
    'BANKBARODA', 'AUBANK', 'FEDERALBNK', 'IDFCFIRSTB', 'PNB', 'BANDHANBNK'
  ]
};

  const filteredStocks = useMemo(() => {
    let filtered = instrumentsList;

    if (selectedIndex && INDEX_CONSTITUENTS[selectedIndex]) {
      const constituents = INDEX_CONSTITUENTS[selectedIndex];
      filtered = filtered.filter(stock => constituents.includes(stock.value));
    }

    if (searchQuery) {
      filtered = filtered.filter(stock => {
        return stock.label.toLowerCase().includes(searchQuery.toLowerCase()) || 
               stock.value.toLowerCase().includes(searchQuery.toLowerCase());
      });
    }

    return filtered.slice(0, 100); // show top 100
  }, [searchQuery, selectedIndex, instrumentsList]);

  const toggleStock = (value: string) => {
    setCurrentSelection(prev => {
      if (prev.includes(value)) {
        return prev.filter(v => v !== value);
      } else {
        if (prev.length >= 50) return prev;
        return [...prev, value];
      }
    });
  };

  const removeStock = (value: string) => {
    setCurrentSelection(prev => prev.filter(v => v !== value));
  };

  const handleSave = () => {
    onSave(currentSelection);
    onClose();
  };

  if (!isOpen || !mounted) return null;

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-surface rounded-xl shadow-2xl w-full max-w-5xl h-[80vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="text-lg font-bold text-foreground">Add Stocks</h2>
          <button onClick={onClose} className="p-2 text-muted hover:text-muted hover:bg-background rounded-full transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 flex overflow-hidden">
          
          {/* Left Panel */}
          <div className="w-1/2 flex flex-col border-r border-border bg-background/50">
            <div className="p-4 space-y-4 border-b border-border">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={16} />
                <input 
                  type="text" 
                  placeholder="Search eg: SBIN, TCS etc" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-surface border border-border rounded-lg text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div className="flex flex-wrap gap-2">
                {INDICES.map(idx => (
                  <button 
                    key={idx}
                    onClick={() => setSelectedIndex(idx === selectedIndex ? null : idx)}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                      selectedIndex === idx 
                        ? 'bg-blue-100 text-blue-700 border border-blue-200' 
                        : 'bg-surface text-muted border border-border hover:bg-background'
                    }`}
                  >
                    {idx}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex px-4 py-2 text-xs font-semibold text-muted border-b border-border">
              <div className="flex-1">Instrument</div>
              <div>Company Name</div>
            </div>

            <div className="flex-1 overflow-y-auto p-2">
              {loading ? (
                <div className="flex flex-col items-center justify-center h-full text-muted gap-2">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                  <span className="text-sm">Loading instruments...</span>
                </div>
              ) : (
                filteredStocks.map((stock, idx) => {
                  const isSelected = currentSelection.includes(stock.value);
                  return (
                  <div 
                    key={`${stock.value}-${idx}`}
                    onClick={() => toggleStock(stock.value)}
                    className="flex items-center justify-between px-2 py-2 hover:bg-surface rounded-lg cursor-pointer transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                        isSelected ? 'bg-blue-600 border-blue-600 text-white' : 'border-border bg-surface group-hover:border-blue-400'
                      }`}>
                        {isSelected && <Check size={12} strokeWidth={3} />}
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-[10px] font-bold">
                          {stock.value.charAt(0)}
                        </div>
                        <span className="text-sm font-semibold text-foreground">{stock.value}</span>
                        <span className="text-[10px] font-medium text-muted bg-surface px-1.5 py-0.5 rounded">NSE</span>
                      </div>
                    </div>
                    <div className="text-xs text-muted truncate max-w-[150px]">
                      {stock.label}
                    </div>
                  </div>
                );
              }))}
            </div>
          </div>

          {/* Right Panel */}
          <div className="w-1/2 flex flex-col bg-surface">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <span className="text-xs font-semibold text-muted">
                Symbol ({currentSelection.length} / 50)
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {currentSelection.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-muted gap-2">
                  <span className="text-sm">No instruments selected</span>
                </div>
              ) : (
                currentSelection.map((symbol, idx) => {
                  const stockInfo = instrumentsList.find(s => s.value === symbol);
                  return (
                    <div key={`${symbol}-${idx}`} className="flex items-center justify-between p-2 hover:bg-background rounded-lg group">
                      <div className="flex items-center gap-3">
                        <button 
                          onClick={() => removeStock(symbol)}
                          className="w-5 h-5 rounded-md border border-border text-muted hover:text-red-500 hover:border-red-200 hover:bg-red-50 flex items-center justify-center transition-colors"
                        >
                          <Minus size={14} />
                        </button>
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-[10px] font-bold">
                            {symbol.charAt(0)}
                          </div>
                          <span className="text-sm font-semibold text-foreground">{symbol}</span>
                          <span className="text-[10px] font-medium text-muted bg-surface px-1.5 py-0.5 rounded">NSE</span>
                        </div>
                      </div>
                      <div className="text-xs text-muted truncate max-w-[150px]">
                        {stockInfo?.label}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            <div className="p-4 border-t border-border flex justify-end bg-background/50">
              <button 
                onClick={handleSave}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
              >
                Done
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>,
    document.body
  );
}
