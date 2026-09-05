# Layouts

## frontend/src/components/layout/InnerHeader.tsx
```tsx
import React from 'react';
import Link from 'next/link';
import { Layers, Bell, Activity } from 'lucide-react';

export default function InnerHeader() {
  return (
    <header className="h-16 bg-[#0F172A]/95 backdrop-blur-xl border-b border-slate-800/80 flex items-center justify-between px-6 sticky top-0 z-50 shadow-[0_4px_30px_rgba(0,0,0,0.1)]">
      <div className="flex items-center gap-6">
        <Link id="header-logo-link" href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 bg-black rounded border border-slate-700 flex items-center justify-center shadow-[0_0_15px_rgba(234,179,8,0.3)] group-hover:scale-105 transition-transform">
            <Layers className="text-yellow-400" size={18} />
          </div>
          <span className="text-xl font-black tracking-tight text-white font-industrial">TRADE<span className="text-yellow-400 drop-shadow-[0_0_8px_rgba(234,179,8,0.5)]">KARO</span></span>
        </Link>

        {/* Fake Terminal Metrics */}
        <div className="hidden lg:flex items-center gap-4 border-l border-slate-800 pl-6">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
            <span className="text-[10px] font-industrial text-slate-400 tracking-widest uppercase">SYS.OK</span>
          </div>
          <div className="flex items-center gap-2">
            <Activity size={12} className="text-teal-500" />
            <span className="text-[10px] font-industrial text-slate-400 tracking-widest uppercase">12ms Ping</span>
          </div>
        </div>
      </div>

      <nav className="hidden md:flex items-center gap-8 font-industrial">
        <Link id="nav-link-dashboard" href="/" className="text-[11px] font-bold text-slate-400 hover:text-white uppercase tracking-widest transition-colors">Dashboard</Link>
        <Link id="nav-link-strategies" href="/strategy" className="text-[11px] font-bold text-yellow-400 uppercase tracking-widest relative">
          Strategies
          <span className="absolute -bottom-6 left-0 right-0 h-[2px] bg-yellow-400 shadow-[0_0_8px_rgba(234,179,8,0.8)]"></span>
        </Link>
        <Link id="nav-link-history" href="/history" className="text-[11px] font-bold text-slate-400 hover:text-white uppercase tracking-widest transition-colors">History</Link>
        <Link id="nav-link-backtests" href="/backtest" className="text-[11px] font-bold text-slate-400 hover:text-white uppercase tracking-widest transition-colors">Backtests</Link>
      </nav>

      <div className="flex items-center gap-5">
        <button className="p-2 text-slate-400 hover:text-yellow-400 hover:bg-slate-800 rounded-full transition-all relative">
          <Bell className="text-xl" size={18} />
          <span className="absolute top-2 right-2 w-2 h-2 bg-rose-500 rounded-full border-2 border-[#0F172A] animate-ping opacity-75"></span>
          <span className="absolute top-2 right-2 w-2 h-2 bg-rose-500 rounded-full border-2 border-[#0F172A]"></span>
        </button>
        <div className="h-6 w-[1px] bg-slate-800 mx-1"></div>
        <div className="flex items-center gap-3 cursor-pointer group hover:bg-slate-800/50 p-1.5 pr-3 rounded-full transition-all border border-transparent hover:border-slate-700">
          <div className="w-8 h-8 bg-slate-800 rounded-full border border-slate-600 p-0.5 overflow-hidden ring-2 ring-transparent group-hover:ring-yellow-400/30 transition-all">
            <img className="rounded-full" src="https://api.dicebear.com/7.x/avataaars/svg?seed=Krish" alt="Avatar" />
          </div>
          <div className="text-left hidden md:block">
            <p className="text-[11px] font-bold text-white font-industrial tracking-wide">KRISH</p>
            <p className="text-[9px] text-yellow-400 font-industrial tracking-widest uppercase opacity-80">PRO</p>
          </div>
        </div>
      </div>
    </header>
  );
}

```

## frontend/src/components/layout/BottomBar.tsx
```tsx
import React from 'react';
import Link from 'next/link';

interface BottomBarProps {
  onConfirm?: () => void;
}

export default function BottomBar({ onConfirm }: BottomBarProps) {
  return (
    <footer className="fixed bottom-0 left-0 right-0 h-20 bg-white border-t border-gray-200 z-50 flex items-center justify-center px-6">
      <div className="max-w-4xl w-full flex items-center justify-between">
        <Link href="/strategy" className="px-6 py-3 text-sm font-bold text-gray-500 hover:text-gray-900 transition-colors">
          Back
        </Link>
        <div className="flex items-center gap-4">
          <p className="hidden md:block text-xs text-gray-400 font-medium italic">Confirming will lock interpretation and start the backtest engine.</p>
          <button id="confirm-continue-btn" onClick={onConfirm} className="px-8 py-3 bg-blue-600 text-white rounded-xl text-sm font-bold shadow-lg shadow-blue-500/20 hover:bg-blue-700 transition-all">
            Confirm & Continue
          </button>
        </div>
      </div>
    </footer>
  );
}

```

## frontend/src/components/layout/DashboardLayout.tsx
```tsx
import React from 'react';
import Header from './Header';
import Sidebar from './Sidebar';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-8 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

```

## frontend/src/components/layout/Header.tsx
```tsx
import React from 'react';
import { Cpu, Search, Bell, Activity } from 'lucide-react';

export default function Header() {
  return (
    <header className="h-16 bg-[#0F172A]/95 backdrop-blur-xl border-b border-slate-800/80 flex items-center justify-between px-6 sticky top-0 z-50 shadow-[0_4px_30px_rgba(0,0,0,0.1)]">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-black rounded border border-slate-700 flex items-center justify-center shadow-[0_0_15px_rgba(234,179,8,0.3)] group-hover:scale-105 transition-transform">
            <Cpu className="text-yellow-400 text-xl" size={18} />
          </div>
          <span className="text-xl font-black text-white tracking-tight font-industrial">TRADE<span className="text-yellow-400 drop-shadow-[0_0_8px_rgba(234,179,8,0.5)]">KARO</span></span>
        </div>
        
        {/* Fake Terminal Metrics */}
        <div className="hidden lg:flex items-center gap-4 border-l border-slate-800 pl-6">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
            <span className="text-[10px] font-industrial text-slate-400 tracking-widest uppercase">SYS.OK</span>
          </div>
          <div className="flex items-center gap-2">
            <Activity size={12} className="text-teal-500" />
            <span className="text-[10px] font-industrial text-slate-400 tracking-widest uppercase">12ms Ping</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-5">
        <button className="p-2 text-slate-400 hover:text-yellow-400 hover:bg-slate-800 rounded-full transition-all">
          <Search className="text-xl" size={18} />
        </button>
        <button className="p-2 text-slate-400 hover:text-yellow-400 hover:bg-slate-800 rounded-full transition-all relative">
          <Bell className="text-xl" size={18} />
          <span className="absolute top-2 right-2 w-2 h-2 bg-rose-500 rounded-full border-2 border-[#0F172A] animate-ping opacity-75"></span>
          <span className="absolute top-2 right-2 w-2 h-2 bg-rose-500 rounded-full border-2 border-[#0F172A]"></span>
        </button>
        <div className="h-6 w-[1px] bg-slate-800 mx-1"></div>
        <div className="flex items-center gap-3 cursor-pointer group hover:bg-slate-800/50 p-1.5 pr-3 rounded-full transition-all border border-transparent hover:border-slate-700">
          <div className="w-8 h-8 bg-slate-800 rounded-full border border-slate-600 p-0.5 overflow-hidden ring-2 ring-transparent group-hover:ring-yellow-400/30 transition-all">
            <img className="rounded-full" src="https://api.dicebear.com/7.x/avataaars/svg?seed=Krish" alt="Avatar" />
          </div>
          <div className="text-left hidden md:block">
            <p className="text-[11px] font-bold text-white font-industrial tracking-wide">KRISH</p>
            <p className="text-[9px] text-yellow-400 font-industrial tracking-widest uppercase opacity-80">PRO</p>
          </div>
        </div>
      </div>
    </header>
  );
}

```

## frontend/src/components/layout/Sidebar.tsx
```tsx
import React from 'react';
import Link from 'next/link';
import { LayoutDashboard, Compass, History, BookOpen } from 'lucide-react';

export default function Sidebar() {
  return (
    <aside className="w-64 bg-[#0F172A] border-r border-slate-800 hidden lg:flex flex-col sticky top-16 h-[calc(100vh-64px)] overflow-y-auto">
      <nav className="flex-1 py-6">
        <div className="px-6 mb-4 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></div>
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest font-industrial">Main Menu</p>
        </div>
        
        <Link id="nav-dashboard" href="/" className="sidebar-item sidebar-item-active">
          <LayoutDashboard className="text-lg" size={18} />
          Dashboard
        </Link>
        <Link id="nav-strategies" href="/strategy" className="sidebar-item">
          <Compass className="text-lg" size={18} />
          Strategies
        </Link>
        <Link id="nav-strategy-history" href="/history" className="sidebar-item">
          <BookOpen className="text-lg" size={18} />
          Strategy History
        </Link>
        <Link id="nav-backtests" href="/backtest" className="sidebar-item">
          <History className="text-lg" size={18} />
          Backtests
        </Link>
      </nav>
    </aside>
  );
}

```

## frontend/src/app/layout.tsx
```tsx
import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from 'next/font/google';
import "./globals.css";

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const jetbrains = JetBrains_Mono({ subsets: ['latin'], variable: '--font-jetbrains' });

export const metadata: Metadata = {
  title: "QuantAI - Institutional Dashboard",
  description: "AI Trading Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrains.variable}`}>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}

```

