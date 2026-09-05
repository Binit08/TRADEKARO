import { create } from 'zustand';

export interface BacktestState {
  // We'll store the AST here temporarily so the backtest page can execute it.
  // In a real DB-backed system, this might be fetched via ID.
  currentAst: any;
  currentCanonical: any;
  
  // The results from the backtest
  backtestResult: any;
  
  // Is it currently running?
  isRunning: boolean;
  
  setStrategyPayload: (ast: any, canonical: any) => void;
  setBacktestResult: (result: any) => void;
  setIsRunning: (running: boolean) => void;
  clearState: () => void;
}

export const useBacktestStore = create<BacktestState>((set) => ({
  currentAst: null,
  currentCanonical: null,
  backtestResult: null,
  isRunning: false,
  
  setStrategyPayload: (ast, canonical) => set({ currentAst: ast, currentCanonical: canonical }),
  setBacktestResult: (result) => set({ backtestResult: result }),
  setIsRunning: (running) => set({ isRunning: running }),
  clearState: () => set({ currentAst: null, currentCanonical: null, backtestResult: null, isRunning: false }),
}));
