"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import {
  Search, Briefcase, FileCode2, Activity, FlaskConical,
  LayoutDashboard, CheckCircle2, XCircle, User, LogOut, Settings, ChevronDown, MonitorPlay
} from 'lucide-react';

export const UserMenu = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [userEmail, setUserEmail] = useState<string>('');
  const [kiteStatus, setKiteStatus] = useState<'loading' | 'connected' | 'disconnected'>('loading');

  useEffect(() => {
    const fetchUserAndStatus = async () => {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.user?.email) {
        setUserEmail(session.user.email);
      }

      try {
        const res = await fetch('/api/auth/kite/status');
        if (res.ok) {
          const data = await res.json();
          setKiteStatus(data.is_connected ? 'connected' : 'disconnected');
        } else {
          setKiteStatus('disconnected');
        }
      } catch (err) {
        setKiteStatus('disconnected');
      }
    };
    fetchUserAndStatus();
  }, []);

  const handleKiteConnect = async () => {
    try {
      const res = await fetch('/api/auth/kite/url');

      if (res.status === 401) {
        window.location.href = '/login';
        return;
      }

      if (res.ok) {
        const data = await res.json();
        if (data.login_url) {
          window.location.href = data.login_url;
        }
      }
    } catch (err) {
      console.error('Failed to connect kite:', err);
    }
  };

  const handleLogout = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    window.location.href = '/login';
  };

  return (
    <div className="relative z-50">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-1.5 rounded-full hover:bg-background transition-colors border border-transparent hover:border-border"
      >
        <div className="w-8 h-8 bg-accent-primary rounded-full flex items-center justify-center text-white shadow-sm">
          <span className="text-xs font-bold">{userEmail ? userEmail.substring(0, 2).toUpperCase() : 'U'}</span>
        </div>
        <ChevronDown size={14} className="text-muted" />
      </button>
      
      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-56 bg-surface rounded-lg shadow-lg border border-border py-1 z-50">
            <div className="px-4 py-3 border-b border-border">
              <p className="text-sm font-bold text-foreground truncate">{userEmail ? userEmail.split('@')[0] : 'User'}</p>
              <p className="text-xs text-muted truncate">{userEmail || 'Loading...'}</p>
            </div>
            
            <div className="px-4 py-3 border-b border-border">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-muted uppercase tracking-wider">Broker</span>
                <div className="flex items-center">
                  {kiteStatus === 'loading' ? (
                    <span className="text-[10px] text-muted">Checking...</span>
                  ) : kiteStatus === 'connected' ? (
                    <>
                      <CheckCircle2 size={10} className="text-green-500 mr-1" />
                      <span className="text-[10px] font-bold text-green-500">Connected</span>
                    </>
                  ) : (
                    <>
                      <XCircle size={10} className="text-red-500 mr-1" />
                      <span className="text-[10px] font-bold text-red-500">Disconnected</span>
                    </>
                  )}
                </div>
              </div>
              
              {kiteStatus !== 'connected' && (
                <button 
                  onClick={handleKiteConnect}
                  className="w-full text-center px-3 py-1.5 text-xs font-bold bg-accent-primary text-white rounded hover:bg-[#152a46] transition-colors"
                >
                  Connect Kite
                </button>
              )}
            </div>
            
            <button className="w-full text-left px-4 py-2.5 text-sm text-foreground hover:bg-background flex items-center gap-2">
              <User size={15} /> Profile
            </button>
            <button className="w-full text-left px-4 py-2.5 text-sm text-foreground hover:bg-background flex items-center gap-2">
              <Settings size={15} /> Settings
            </button>
            <div className="h-px bg-surface my-1" />
            <button 
              onClick={handleLogout}
              className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
            >
              <LogOut size={15} /> Logout
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export const NavBar = ({ activeTab, onTabChange, onCreateStrategy }: { activeTab: string; onTabChange: (tab: string) => void; onCreateStrategy: () => void }) => {
  const router = useRouter();

  const tabs = [
    { name: 'Dashboard', icon: LayoutDashboard },
    { name: 'Create Strategy', icon: FileCode2 },
    { name: 'Screeners', icon: Search },
    { name: 'Portfolio', icon: Briefcase },
    { name: 'Strategies', icon: Activity },
    { name: 'Backtests', icon: FlaskConical },
    { name: 'Paper Trade', icon: MonitorPlay },
  ];

  return (
    <nav
      className="w-full flex items-center justify-between px-6 bg-surface border-b border-border"
      style={{ height: '52px' }}
    >
      <div 
        className="flex space-x-1 h-full overflow-x-auto overflow-y-hidden [&::-webkit-scrollbar]:hidden"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.name;
          const Icon = tab.icon;
          return (
            <button
              key={tab.name}
              onClick={() => {
                if (tab.name === 'Create Strategy') {
                  onCreateStrategy();
                  return;
                }
                
                onTabChange(tab.name);
              }}
              className={`relative h-full flex items-center space-x-2 px-4 transition-colors focus:outline-none focus-visible:bg-background whitespace-nowrap ${isActive ? 'text-accent-primary font-bold' : 'text-muted font-semibold'}`}
              style={{
                fontFamily: '"Space Grotesk", sans-serif',
              }}
            >
              <Icon size={16} strokeWidth={isActive ? 2.5 : 2} className="shrink-0" />
              <span className="text-sm">{tab.name}</span>
              {isActive && (
                <div
                  className="absolute bottom-[-1px] left-0 w-full h-[2px] bg-accent-primary"
                />
              )}
            </button>
          );
        })}
      </div>
      <div className="ml-4 shrink-0">
        <UserMenu />
      </div>
    </nav>
  );
};
