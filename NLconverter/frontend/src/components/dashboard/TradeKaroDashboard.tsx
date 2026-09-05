"use client";

import React, { useState } from 'react';
import { StrategyHistoryList } from '@/components/strategy/StrategyHistoryList';
import { BacktestHistoryList } from '@/components/backtest/BacktestHistoryList';
import CreateStrategyWizardModal from '@/components/strategy/CreateStrategyWizardModal';
import PaperTradeView from '@/components/papertrade/PaperTradeView';
import { NavBar } from '@/components/layout/Navigation';
import { IndexTape, Watchlist, Screener } from '@/components/dashboard/TradingViewWidgets';
import { LiveTradesPanel, PastTrades, BrokerConnectionPanel } from '@/components/dashboard/TradeWidgets';

export default function TradeKaroDashboard({ initialTab = 'Dashboard' }: { initialTab?: string }) {
  const [activeTab, setActiveTab] = useState(initialTab);
  const [isWizardOpen, setIsWizardOpen] = useState(false);

  return (
    <div className="min-h-screen w-full flex flex-col bg-background">
      <IndexTape />
      <NavBar 
        activeTab={activeTab} 
        onTabChange={setActiveTab} 
        onCreateStrategy={() => setIsWizardOpen(true)}
      />
      <CreateStrategyWizardModal isOpen={isWizardOpen} onClose={() => setIsWizardOpen(false)} />

      {/* Main Content Grid */}
      <main className="flex-1 p-6">
        {activeTab === 'Screeners' ? (
          <div className="w-full">
            <Screener />
          </div>
        ) : activeTab === 'Strategies' ? (
          <div className="w-full space-y-5">
            <div>
              <h1
                className="text-2xl font-bold text-foreground"
                style={{ fontFamily: '"Space Grotesk", sans-serif' }}
              >
                Strategies
              </h1>
              <p className="mt-1 text-sm text-muted">
                All saved strategies, newest first.
              </p>
            </div>
            <StrategyHistoryList loadAll />
          </div>
        ) : activeTab === 'Backtests' ? (
          <div className="w-full">
            <BacktestHistoryList />
          </div>
        ) : activeTab === 'Paper Trade' ? (
          <div className="w-full -m-6">
            <PaperTradeView onNavigateToStrategies={() => setActiveTab('Strategies')} />
          </div>
        ) : (
          <div className="w-full min-h-[calc(100vh-140px)] grid grid-cols-1 lg:grid-cols-12 gap-5">
            {/* Left/Center columns - Live Trades */}
            <LiveTradesPanel />

            {/* Right column - Split vertically */}
            {activeTab === 'Dashboard' && (
              <div className="col-span-1 lg:col-span-5 flex flex-col gap-5 h-full">
                <BrokerConnectionPanel />
                <Watchlist />
                <PastTrades />
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
