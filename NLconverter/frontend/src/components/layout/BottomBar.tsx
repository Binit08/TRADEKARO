import React from 'react';
import Link from 'next/link';

interface BottomBarProps {
  onConfirm?: () => void;
}

export default function BottomBar({ onConfirm }: BottomBarProps) {
  return (
    <footer className="fixed bottom-0 left-0 right-0 h-20 bg-surface border-t border-border z-50 flex items-center justify-center px-6">
      <div className="max-w-4xl w-full flex items-center justify-between">
        <Link href="/strategy" className="px-6 py-3 text-sm font-bold text-muted hover:text-foreground transition-colors">
          Back
        </Link>
        <div className="flex items-center gap-4">
          <p className="hidden md:block text-xs text-muted font-medium italic">Confirming will lock interpretation and start the backtest engine.</p>
          <button id="confirm-continue-btn" onClick={onConfirm} className="px-8 py-3 bg-blue-600 text-white rounded-xl text-sm font-bold shadow-lg shadow-blue-500/20 hover:bg-blue-700 transition-all">
            Confirm & Continue
          </button>
        </div>
      </div>
    </footer>
  );
}
