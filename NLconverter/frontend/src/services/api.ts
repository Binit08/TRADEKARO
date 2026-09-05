/**
 * Fix 1: All backend calls go through Next.js server-side proxy routes.
 *        No API keys are sent from the browser.
 * Fix 3: Properly typed getBacktests() with BacktestListItem interface.
 * Fix 4: runBacktest returns backtest_id from backend (single source of truth).
 *        saveBacktest() is removed — backend persists on its own.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface ExecutionContext {
  universe: {
    index: string;
    exchange: string;
    asset_class: string;
  };
  timeframe: string;
  capital_per_trade: {
    amount: number;
    currency: string;
  };
  position_side: string;
  order_type: string;
  max_concurrent_positions: number;
  stock?: string;
}

export interface StrategyGenerateRequest {
  prompt: string;
  execution_context: ExecutionContext;
  semantic_resolutions?: any[];
}

export interface BacktestParams {
  strategy_id?: string | number;
  strategy_ast: any;
  start_date: string;
  end_date: string;
  initial_capital: number;
  position_size: number;
  position_size_type?: string;
  commission_rate?: number;
  slippage_bps?: number;
  allow_short: boolean;
  symbol: string;
  symbols?: string[];
  timeframe: string;
  exchange?: string;
  market_type?: string;
  multiplier?: number;
  margin?: number;
  expiry?: string;
}

/** Fix 3: Explicit return type for getBacktests() */
export interface BacktestListItem {
  id: number;
  symbol: string;
  timeframe: string;
  start_date: string;
  end_date: string;
  initial_cash: number;
  position_size: number;
  position_size_type: string;
  net_profit: number;
  total_return: number;
  win_rate: number;
  total_trades: number;
  status: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Strategy APIs — routed through /api/proxy/* (Fix 1)
// ---------------------------------------------------------------------------

export const generateStrategy = async (req: StrategyGenerateRequest) => {
  const response = await fetch('/api/proxy/strategy', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });

  const text = await response.text();
  let data: any;
  try {
    data = JSON.parse(text);
  } catch {
    data = { detail: text || response.statusText || 'Internal Server Error' };
  }

  if (!response.ok) {
    throw new Error(data.detail || data.message || 'Failed to generate strategy');
  }
  return data;
};

export const getStrategyHistory = async (limit = 10, offset = 0) => {
  const response = await fetch(`/api/proxy/strategies?limit=${limit}&offset=${offset}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  const text = await response.text();
  let data: any;
  try {
    data = JSON.parse(text);
  } catch {
    data = { detail: text || response.statusText || 'Internal Server Error' };
  }

  if (!response.ok) {
    throw new Error(data.detail || data.message || 'Failed to fetch strategy history');
  }
  return data;
};

// ---------------------------------------------------------------------------
// Backtest APIs
// ---------------------------------------------------------------------------

/**
 * Fix 4: runBacktest now returns { ...result, backtest_id } from backend.
 * The backend is the single source of truth — it persists the record.
 */
export const runBacktest = async (params: BacktestParams) => {
  const formattedSymbol = params.symbol.trim().toUpperCase();

  const backendPayload = {
    symbol: formattedSymbol,
    symbols: params.symbols,
    exchange: params.exchange || 'NSE',
    start: params.start_date,
    end: params.end_date,
    timeframe: params.timeframe,
    strategy_id: params.strategy_id,
    strategy_ast: params.strategy_ast,
    initial_cash: params.initial_capital,
    position_size_type: params.position_size_type || 'fixed_qty',
    position_size: params.position_size,
    commission_rate: params.commission_rate ?? 0.0001,
    slippage_bps: params.slippage_bps ?? 2.0,
    allow_short: params.allow_short,
    market_type: params.market_type || 'equity',
    multiplier: params.multiplier,
    margin: params.margin,
    expiry: params.expiry,
  };

  // Fix 1: Route through server-side proxy — no API key in browser
  const response = await fetch('/api/proxy/backtest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(backendPayload),
  });

  const text = await response.text();
  let data: any;
  try {
    data = JSON.parse(text);
  } catch {
    data = { detail: text || response.statusText || 'Internal Server Error' };
  }

  if (!response.ok) {
    const error: any = new Error(
      typeof data.detail === 'string' ? data.detail : 'Failed to run backtest'
    );
    error.details = data.detail || data.message || data;
    throw error;
  }
  return data;
};

/**
 * Fix 4: saveBacktest is REMOVED — the backend persists backtests directly.
 * The frontend no longer duplicates writes.
 */

// ---------------------------------------------------------------------------
// Backtest read APIs — Next.js API routes proxy to backend (Fix 4)
// ---------------------------------------------------------------------------

export const getBacktest = async (id: string) => {
  const response = await fetch(`/api/backtests/${id}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });
  const text = await response.text();
  let result: any;
  try {
    result = JSON.parse(text);
  } catch {
    result = { error: text || response.statusText || 'Internal Server Error' };
  }
  if (!response.ok || !result.data) {
    throw new Error(result.error || result.detail || 'Failed to fetch backtest');
  }
  return result.data;
};

export interface PaginatedBacktests {
  data: BacktestListItem[];
  has_more: boolean;
  total_count: number;
}

export const getBacktests = async (limit = 10, offset = 0): Promise<PaginatedBacktests> => {
  const response = await fetch(`/api/backtests?limit=${limit}&offset=${offset}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });
  const text = await response.text();
  let result: any;
  try {
    result = JSON.parse(text);
  } catch {
    result = { error: text || response.statusText || 'Internal Server Error' };
  }
  if (!response.ok || !result.data) {
    throw new Error(result.error || result.detail || 'Failed to fetch backtests');
  }
  return result; // return { data, has_more, total_count }
};

// ---------------------------------------------------------------------------
// Paper Trading APIs
// ---------------------------------------------------------------------------

export interface PaperTradeParams {
  symbols: string[];
  timeframe: string;
  strategy_ast: any;
  exchange?: string;
  initial_cash?: number;
  position_size?: number;
}

export const startPaperTrade = async (params: PaperTradeParams) => {
  const backendPayload = {
    symbols: params.symbols.map(s => s.trim().toUpperCase()),
    timeframe: params.timeframe || '1m',
    strategy_ast: params.strategy_ast,
    exchange: params.exchange || 'NSE',
    initial_cash: params.initial_cash || 100000.0,
    position_size: params.position_size || 1.0,
  };

  const response = await fetch('/api/proxy/paper_trade/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(backendPayload),
  });

  const text = await response.text();
  let data: any;
  try {
    data = JSON.parse(text);
  } catch {
    data = { detail: text || response.statusText || 'Internal Server Error' };
  }

  if (!response.ok) {
    const error: any = new Error(
      typeof data.detail === 'string' ? data.detail : 'Failed to start paper trade'
    );
    error.details = data.detail || data.message || data;
    throw error;
  }
  return data;
};

export const getPaperTradeSessions = async () => {
  const response = await fetch('/api/proxy/paper_trade/sessions', {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  const text = await response.text();
  let data: any;
  try {
    data = JSON.parse(text);
  } catch {
    data = { detail: text || response.statusText || 'Internal Server Error' };
  }

  if (!response.ok) {
    throw new Error(data.detail || data.error || 'Failed to fetch paper trade sessions');
  }
  
  return data.sessions || [];
};
