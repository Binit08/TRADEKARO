"use client";
import React, { useState } from 'react';
import Link from 'next/link';
import { LayoutDashboard, Compass, History, BookOpen } from 'lucide-react';
import CreateStrategyWizardModal from '../strategy/CreateStrategyWizardModal';

export default function Sidebar() {
  const [isWizardOpen, setIsWizardOpen] = useState(false);

  return (
    <aside className="w-64 bg-background border-r border-slate-800 hidden lg:flex flex-col sticky top-16 h-[calc(100vh-64px)] overflow-y-auto">
      <nav className="flex-1 py-6">
        <div className="px-6 mb-4 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></div>
          <p className="text-[10px] font-bold text-muted uppercase tracking-widest font-industrial">Main Menu</p>
        </div>
        
        <Link id="nav-dashboard" href="/" className="sidebar-item sidebar-item-active">
          <LayoutDashboard className="text-lg" size={18} />
          Dashboard
        </Link>
        <button 
          id="nav-strategies" 
          onClick={() => setIsWizardOpen(true)} 
          className="sidebar-item w-full text-left flex items-center gap-3 px-6 py-3"
        >
          <Compass className="text-lg" size={18} />
          Strategies
        </button>
        <Link id="nav-strategy-history" href="/history" className="sidebar-item">
          <BookOpen className="text-lg" size={18} />
          Strategy History
        </Link>
        <Link id="nav-backtests" href="/backtest" className="sidebar-item">
          <History className="text-lg" size={18} />
          Backtests
        </Link>
        <Link id="nav-brokers" href="/settings/brokers" className="sidebar-item">
          Brokers
        </Link>
      </nav>

      <CreateStrategyWizardModal 
        isOpen={isWizardOpen} 
        onClose={() => setIsWizardOpen(false)} 
      />
    </aside>
  );
}
