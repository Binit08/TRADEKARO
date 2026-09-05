import React from 'react';
import { Cpu, Search, Bell, Activity } from 'lucide-react';

export default function Header() {
  return (
    <header className="h-16 bg-background/95 backdrop-blur-xl border-b border-slate-800/80 flex items-center justify-between px-6 sticky top-0 z-50 shadow-[0_4px_30px_rgba(0,0,0,0.1)]">
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
            <span className="text-[10px] font-industrial text-muted tracking-widest uppercase">SYS.OK</span>
          </div>
          <div className="flex items-center gap-2">
            <Activity size={12} className="text-teal-500" />
            <span className="text-[10px] font-industrial text-muted tracking-widest uppercase">12ms Ping</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-5">
        <button className="p-2 text-muted hover:text-yellow-400 hover:bg-slate-800 rounded-full transition-all">
          <Search className="text-xl" size={18} />
        </button>
        <button className="p-2 text-muted hover:text-yellow-400 hover:bg-slate-800 rounded-full transition-all relative">
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
