"use client";
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import ExecutionContextForm from '@/components/strategy/ExecutionContextForm';
import NaturalLanguageEditor from '@/components/strategy/NaturalLanguageEditor';

export default function CreateStrategyPage() {
  const router = useRouter();
  const [executionContext, setExecutionContext] = useState({
    universe: {
      index: 'NIFTY_50',
      exchange: 'NSE',
      asset_class: 'equity',
    },
    timeframe: '1m',
    position_side: 'LONG',
    order_type: 'MAK',
    stocks: [],
    future_contract: {
      underlying: '',
      expiry: '',
      lot_size: 0,
      margin: 0,
    }
  });

  const [strategyType, setStrategyType] = useState<'equity' | 'future'>('equity');

  useEffect(() => {
    const meta = localStorage.getItem('strategy_metadata');
    if (meta) {
      try {
        const parsed = JSON.parse(meta);
        if (parsed.type) {
          setStrategyType(parsed.type);
        }
      } catch {}
    }

    const savedContext = localStorage.getItem('draft_execution_context');
    if (savedContext) {
      try {
        setExecutionContext(JSON.parse(savedContext));
      } catch {}
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('draft_execution_context', JSON.stringify(executionContext));
  }, [executionContext]);

  return (
    <div className="min-h-screen p-4 md:p-6 lg:px-8 lg:py-4 bg-background text-foreground flex flex-col overflow-y-auto">
      <div className="w-full px-6 flex-1 flex flex-col">
        <header className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4 mt-4 shrink-0">
          <div className="flex items-start gap-5">
            <Link id="back-link" href="/" className="flex items-center justify-center w-10 h-10 rounded-xl bg-surface border border-border shadow-sm hover:bg-background transition-soft text-foreground">
              <ArrowLeft className="text-xl" size={20} />
            </Link>
            <div>
              <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">Create New Strategy</h1>
            </div>
          </div>
          
          <div className="flex items-center gap-6">
            <button onClick={() => router.push('/')} className="px-6 py-2.5 rounded-xl bg-surface border border-border shadow-sm font-bold transition-soft hover:bg-background text-foreground">
              Cancel
            </button>
            <button onClick={() => {
              localStorage.setItem('draft_execution_context', JSON.stringify(executionContext));
              alert('Draft saved to local storage.');
            }} className="px-6 py-2.5 rounded-xl bg-surface border border-border shadow-sm font-bold transition-soft hover:bg-background text-foreground">
              Save Draft
            </button>
          </div>
        </header>
        
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch flex-1 min-h-0 pb-4">
          <ExecutionContextForm 
            context={executionContext}
            setContext={setExecutionContext}
            strategyType={strategyType}
          />
          <NaturalLanguageEditor 
            executionContext={executionContext}
            strategyType={strategyType}
          />
        </div>
      </div>
    </div>
  );
}
