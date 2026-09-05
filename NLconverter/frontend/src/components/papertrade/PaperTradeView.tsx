"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useState, useEffect } from "react";
import PaperTradeChart from "@/components/charts/PaperTradeChart";
import { getPaperTradeSessions } from "@/services/api";
import Loader from "@/components/ui/Loader";

function ActiveSessionsList({ onNavigateToStrategies }: { onNavigateToStrategies?: () => void }) {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    getPaperTradeSessions().then(data => {
      setSessions(data);
    }).catch(err => {
      console.error("Failed to fetch sessions", err);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-64">
      <Loader />
      <p className="text-muted text-sm mt-4">Loading active sessions...</p>
    </div>
  );

  return (
    <div className="w-full">
      <h2 className="text-2xl font-bold text-foreground mb-6">Active Paper Trading Sessions</h2>
      {sessions.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-[40vh] text-center border border-dashed border-border rounded-2xl bg-surface shadow-sm">
          <h3 className="text-xl font-semibold text-foreground mb-2">No Active Sessions</h3>
          <p className="text-muted max-w-md mb-6">
            You don't have any paper trading sessions running. Start one from the Strategies tab.
          </p>
          <button 
            onClick={onNavigateToStrategies}
            className="px-6 py-2.5 bg-accent-primary hover:bg-[#152a46] text-white rounded-lg font-bold transition-colors shadow-sm"
          >
            Go to Strategies
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sessions.map(s => (
            <div 
              key={s.session_id} 
              className="bg-surface border border-border p-6 rounded-2xl shadow-sm hover:border-emerald-300 hover:shadow-md cursor-pointer transition-all flex flex-col" 
              onClick={() => router.push(`?sessionId=${s.session_id}`)}
            >
              <div className="flex justify-between items-center mb-4">
                <span className="font-bold text-lg text-foreground">{s.symbols.join(', ')}</span>
                <span className={`px-2.5 py-1 text-xs font-bold uppercase tracking-wider rounded-full ${s.status === 'RUNNING' ? 'bg-emerald-50 border border-emerald-100 text-emerald-600' : 'bg-background border border-border text-muted'}`}>
                  {s.status}
                </span>
              </div>
              <div className="text-xs text-muted font-mono truncate bg-background p-2 rounded-lg border border-border">
                {s.session_id}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PaperTradeContent({ onNavigateToStrategies }: { onNavigateToStrategies?: () => void }) {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("sessionId");
  const [metrics, setMetrics] = useState({ pnl: '--', positions: '--', trades: '--' });

  useEffect(() => {
    if (!sessionId) return;
    const fetchStatus = async () => {
      try {
        const res = await fetch(`/api/proxy/paper_trade/${sessionId}/status`);
        if (res.status === 404) { alert("This session does not exist (it may have crashed during creation). Please go back and start a new session."); clearInterval(interval); window.location.href = "/strategy/review"; return; }
        if (res.ok) {
          const data = await res.json();
          if (data) {
            const pnl = data.aggregate_pnl !== undefined ? data.aggregate_pnl.toFixed(2) : '--';
            const activePositions = data.active_positions_count !== undefined ? data.active_positions_count : '--';
            
            setMetrics({
              pnl: pnl !== '--' ? `₹${pnl}` : '--',
              positions: activePositions.toString(),
              trades: data.trades_executed !== undefined ? data.trades_executed.toString() : '--'
            });
          }
        }
      } catch (err) {
        console.error("Failed to fetch paper trade status", err);
      }
    };
    
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, [sessionId]);

  if (!sessionId) {
    return <ActiveSessionsList onNavigateToStrategies={onNavigateToStrategies} />;
  }

  return (
    <div className="w-full flex flex-col space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
        <div>
          <h1 className="text-3xl font-bold text-foreground tracking-tight">Live Paper Trading</h1>
          <p className="text-muted mt-1">Monitoring active market stream and strategy execution.</p>
        </div>
        <div className="mt-4 md:mt-0 flex space-x-3">
          <button 
            className="px-4 py-2 bg-surface border border-border text-foreground rounded-lg shadow-sm hover:bg-background font-medium text-sm transition-colors"
            onClick={() => window.location.reload()}
          >
            Refresh Stream
          </button>
          <button 
            className="px-4 py-2 bg-red-50 text-red-600 border border-red-100 rounded-lg shadow-sm hover:bg-red-100 font-medium text-sm transition-colors"
            onClick={async () => {
              await fetch(`/api/proxy/paper_trade/${sessionId}/stop`, { method: "POST" });
              alert("Paper trading session stopped.");
            }}
          >
            Stop Trading
          </button>
        </div>
      </div>

      {/* Main Chart Area */}
      <div className="w-full">
        <PaperTradeChart sessionId={sessionId} />
      </div>

      {/* Live Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-surface p-6 rounded-xl border border-border shadow-sm">
          <h3 className="text-sm font-medium text-muted">Live PnL</h3>
          <p className={`text-2xl font-bold mt-2 ${metrics.pnl.startsWith('₹-') ? 'text-red-500' : (metrics.pnl !== '--' ? 'text-emerald-500' : 'text-foreground')}`}>
            {metrics.pnl}
          </p>
        </div>
        <div className="bg-surface p-6 rounded-xl border border-border shadow-sm">
          <h3 className="text-sm font-medium text-muted">Active Positions</h3>
          <p className="text-2xl font-bold text-foreground mt-2">{metrics.positions}</p>
        </div>
        <div className="bg-surface p-6 rounded-xl border border-border shadow-sm">
          <h3 className="text-sm font-medium text-muted">Total Trades</h3>
          <p className="text-2xl font-bold text-foreground mt-2">{metrics.trades}</p>
        </div>
      </div>
    </div>
  );
}

export default function PaperTradeView({ onNavigateToStrategies }: { onNavigateToStrategies?: () => void }) {
  return (
    <div className="min-h-screen bg-background p-6 md:p-12">
      <div className="max-w-7xl mx-auto">
        <Suspense fallback={<div className="flex flex-col items-center justify-center h-64"><Loader /><p className="text-muted text-sm mt-4">Loading session...</p></div>}>
          <PaperTradeContent onNavigateToStrategies={onNavigateToStrategies} />
        </Suspense>
      </div>
    </div>
  );
}
