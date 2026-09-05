"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Link, CheckCircle2, XCircle, Activity, TrendingUp, TrendingDown } from 'lucide-react';
import { Panel } from '@/components/ui/Panel';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';

const PAST_TRADES = [
  { symbol: 'MARUTI', closedDate: '22 Jul, 14:30', pnl: 8500.00, isUp: true },
  { symbol: 'WIPRO', closedDate: '21 Jul, 11:15', pnl: -2100.50, isUp: false },
  { symbol: 'HINDUNILVR', closedDate: '20 Jul, 15:00', pnl: 3400.00, isUp: true },
  { symbol: 'AXISBANK', closedDate: '19 Jul, 09:45', pnl: 5600.25, isUp: true },
];

export const LiveTradesPanel = () => {
  const [trades, setTrades] = useState<any[]>([]);
  const [status, setStatus] = useState<'loading' | 'connected' | 'disconnected' | 'error'>('loading');

  useEffect(() => {
    const fetchPositions = async () => {
      try {
        const res = await fetch('/api/portfolio/positions');

        if (res.status === 401) {
          setStatus('disconnected');
          return;
        }

        if (res.ok) {
          const data = await res.json();
          setTrades(data.positions || []);
          setStatus('connected');
        } else {
          setStatus('error');
        }
      } catch (err) {
        console.error('Failed to fetch positions:', err);
        setStatus('error');
      }
    };

    fetchPositions();
  }, []);

  if (status === 'disconnected') {
    return (
      <Panel title="Current Live Trades" className="col-span-1 lg:col-span-7 h-full">
        <EmptyState 
          icon={Link} 
          title="Not Connected to Broker" 
          description="Connect your Kite account in the Broker Connection panel to view your live portfolio and open positions." 
        />
      </Panel>
    );
  }

  return (
    <Panel
      title="Current Live Trades"
      headerRight={
        <span
          className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-accent-secondary text-accent-primary"
        >
          {status === 'loading' ? 'LOADING...' : `${trades.length} OPEN`}
        </span>
      }
      className="col-span-1 lg:col-span-7 h-full"
    >
      <div className="w-full overflow-x-auto">
        <table className="w-full text-left" style={{ fontFamily: '"Inter", sans-serif' }}>
          <thead>
            <tr
              className="text-xs uppercase tracking-wider border-b text-muted border-border"
            >
              <th className="pb-3 font-medium">Stock Name</th>
              <th className="pb-3 font-medium text-right">Qty</th>
              <th className="pb-3 font-medium text-right">LTP</th>
              <th className="pb-3 font-medium text-right">P&L</th>
              <th className="pb-3 font-medium text-right">% Change</th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {status === 'loading' ? (
              <tr>
                <td colSpan={5} className="p-4">
                  <Skeleton count={5} className="h-12 w-full mb-2" />
                </td>
              </tr>
            ) : trades.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-4">
                  <EmptyState icon={Activity} title="No Open Positions" description="You do not have any open positions right now." />
                </td>
              </tr>
            ) : (
              trades.map((trade, idx) => (
                <tr
                  key={idx}
                  className="border-b last:border-b-0 hover:bg-background transition-colors group border-border"
                >
                  <td className="py-4 font-bold text-foreground" style={{ fontFamily: '"Space Grotesk", sans-serif' }}>
                    {trade.symbol}
                  </td>
                  <td className="py-4 text-right font-mono tabular-nums text-foreground">
                    {trade.qty}
                  </td>
                  <td className="py-4 text-right font-mono tabular-nums text-foreground">
                    ₹{trade.ltp.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className={`py-4 text-right font-mono tabular-nums ${trade.isUp ? 'text-status-win' : 'text-status-loss'}`}>
                    <div className="flex items-center justify-end">
                      {trade.isUp ? <TrendingUp size={14} className="mr-1.5 opacity-80" /> : <TrendingDown size={14} className="mr-1.5 opacity-80" />}
                      {trade.pnl > 0 ? '+' : ''}{trade.pnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </div>
                  </td>
                  <td className={`py-4 text-right font-mono tabular-nums font-medium ${trade.isUp ? 'text-status-win' : 'text-status-loss'}`}>
                    {trade.pnlPct > 0 ? '+' : ''}{trade.pnlPct.toFixed(2)}%
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Panel>
  );
};

export const PastTrades = () => {
  return (
    <Panel title="Past Trades" className="flex-1">
      <div className="space-y-4">
        {PAST_TRADES.map((trade, idx) => (
          <div key={idx} className="flex justify-between items-center opacity-85 group hover:opacity-100 transition-opacity">
            <div className="flex flex-col">
              <span className="font-bold text-sm text-foreground" style={{ fontFamily: '"Space Grotesk", sans-serif' }}>
                {trade.symbol}
              </span>
              <span className="text-xs mt-0.5 text-muted" style={{ fontFamily: '"Inter", sans-serif' }}>
                {trade.closedDate}
              </span>
            </div>
            <span
              className={`tabular-nums text-sm font-medium ${trade.isUp ? 'text-status-win' : 'text-status-loss'}`}
            >
              {trade.pnl > 0 ? '+' : ''}{trade.pnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>
        ))}
      </div>
    </Panel>
  );
};

// --- Broker Connection Panel ---
export const BrokerConnectionPanel = () => {
  const [status, setStatus] = useState<'loading' | 'connected' | 'disconnected'>('loading');
  const [activeBroker, setActiveBroker] = useState<any>(null);
  const router = useRouter();
  
  useEffect(() => {
    const fetchBrokers = async () => {
      try {
        const res = await fetch('/api/v1/brokers/');
        
        if (res.ok) {
          const brokers = await res.json();
          const active = brokers.find((b: any) => b.is_active);
          if (active) {
            setActiveBroker(active);
            setStatus('connected');
          } else {
            setStatus('disconnected');
          }
        } else {
          setStatus('disconnected');
        }
      } catch (err) {
        console.error('Failed to fetch broker status:', err);
        setStatus('disconnected');
      }
    };
    
    fetchBrokers();
  }, []);

  return (
    <Panel title="Broker Connection" className="mb-5">
      <div className="flex items-center justify-between p-2">
        <div className="flex items-center space-x-4">
          <div className="w-10 h-10 rounded-full bg-zinc-100 flex items-center justify-center">
            <Link size={20} className={status === 'connected' ? 'text-green-600' : 'text-zinc-400'} />
          </div>
          <div>
            <h3 className="font-medium text-sm text-foreground">
              {activeBroker ? activeBroker.broker_name : 'No Active Broker'}
            </h3>
            <div className="flex items-center mt-1">
              {status === 'loading' ? (
                <span className="text-xs text-muted">Checking status...</span>
              ) : status === 'connected' ? (
                <>
                  <CheckCircle2 size={12} className="text-green-600 mr-1" />
                  <span className="text-xs font-medium text-green-600">Connected</span>
                </>
              ) : (
                <>
                  <XCircle size={12} className="text-red-500 mr-1" />
                  <span className="text-xs font-medium text-red-500">Not Connected</span>
                </>
              )}
            </div>
          </div>
        </div>
        
        <button
          onClick={() => router.push('/settings/brokers')}
          className="text-xs font-medium px-4 py-2 bg-accent-primary text-white rounded hover:bg-[#152a46] transition-colors"
        >
          Manage
        </button>
      </div>
    </Panel>
  );
};
