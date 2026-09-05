"use client";
import React, { useState, useEffect } from 'react';
import { Wand2, Sparkles, Info, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';
import StrategySummary from './StrategySummary';
import BacktestConfigModal from './BacktestConfigModal';
import { AIClarificationModal } from './AIClarificationModal';

/**
 * Fix 1: All fetch calls use relative URLs through Next.js proxy routes.
 *        No API key headers are sent from the browser.
 * Fix 6: Character counter shown below textarea. Clarification retry cap = 5.
 */

const MAX_PROMPT_LENGTH = 10000;
const MAX_CLARIFICATION_RETRIES = 5;

type Blocker = {
  reason: string;
  question: string;
};

type ApprovalItem = {
  type: string;
  source: string;
  candidates: string[];
  confidence: number;
};

export type StrategyResult = {
  status: string;
  prompt: string;
  canonical_json?: Record<string, unknown>;
  ast_json?: Record<string, unknown>;
  blockers?: Blocker[];
  approval_items?: ApprovalItem[];
  current_strategy?: string;
  message?: string;
};

interface NaturalLanguageEditorProps {
  executionContext: {
    universe: {
      index: string;
      exchange: string;
      asset_class: string;
    };
    timeframe: string;
    position_side: string;
    order_type?: string;
    stock?: string;
    stocks?: string[];
    future_contract?: {
      underlying: string;
      expiry: string;
      lot_size: number;
      margin: number;
      multiplier?: number;
    };
  };
  strategyType?: 'equity' | 'future';
}

export default function NaturalLanguageEditor({ executionContext, strategyType = 'equity' }: NaturalLanguageEditorProps) {
  const [entryCondition, setEntryCondition] = useState('');
  const [exitCondition, setExitCondition] = useState('');
  const [strategyName, setStrategyName] = useState('');
  const [strategyTag, setStrategyTag] = useState('');
  const [strategyDescription, setStrategyDescription] = useState('');

  // Persist Editor State
  useEffect(() => {
    const savedEntry = localStorage.getItem('draft_entry_condition');
    const savedExit = localStorage.getItem('draft_exit_condition');
    if (savedEntry) setEntryCondition(savedEntry);
    if (savedExit) setExitCondition(savedExit);

    const savedMetaStr = localStorage.getItem('strategy_metadata');
    if (savedMetaStr) {
      try {
        const meta = JSON.parse(savedMetaStr);
        if (meta.name) setStrategyName(meta.name);
        if (meta.tags && meta.tags.length > 0) setStrategyTag(meta.tags.join(', '));
        else if (meta.category) setStrategyTag(meta.category); // Fallback to category if no tags
        if (meta.description) setStrategyDescription(meta.description);
      } catch (e) {}
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('draft_entry_condition', entryCondition);
  }, [entryCondition]);

  useEffect(() => {
    localStorage.setItem('draft_exit_condition', exitCondition);
  }, [exitCondition]);



  const content = (entryCondition.trim() || exitCondition.trim()) 
    ? `Entry Condition: ${entryCondition}\nExit Condition: ${exitCondition}` 
    : '';
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | string[] | null>(null);
  const [result, setResult] = useState<StrategyResult | null>(null);
  const [currentStrategyText, setCurrentStrategyText] = useState('');
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [clarificationCount, setClarificationCount] = useState(0);

  const isEquity = strategyType === 'equity';

  const isContextValid = true;

  // Fix 6: Character counter helpers
  const remaining = MAX_PROMPT_LENGTH - content.length;
  const isOverLimit = remaining < 0;

  const resetInteractiveState = () => {
    setCurrentStrategyText('');
    setShowConfigModal(false);
    setClarificationCount(0);
    setError(null);
  };

  const handleGenerateStrategy = async () => {
    if (!content.trim()) {
      setError('Please enter a strategy prompt.');
      return;
    }

    // Fix 6: Client-side prompt length check
    if (content.length > MAX_PROMPT_LENGTH) {
      setError(`Prompt exceeds maximum length of ${MAX_PROMPT_LENGTH.toLocaleString()} characters.`);
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    resetInteractiveState();

    const initialPrompt = content.trim();
    setCurrentStrategyText(initialPrompt);

    try {
      // Fix 1: Route through server-side proxy — no API key in browser
      const response = await fetch('/api/proxy/strategy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: strategyName.trim() || undefined,
          tag: strategyTag.trim() || undefined,
          description: strategyDescription.trim() || undefined,
          prompt: initialPrompt,
          market_type: isEquity ? 'equity' : 'futures',
          execution_context: executionContext
        }),
      });

      const text = await response.text();
      let data: any;
      try {
        data = JSON.parse(text);
      } catch {
        throw new Error(`Server returned invalid response (500). Backend might be down or crashed. Raw: ${text.substring(0, 100)}...`);
      }

      if (!response.ok) {
        if (data.detail && typeof data.detail === 'object' && Array.isArray(data.detail.messages)) {
          setError(data.detail.messages);
          setLoading(false);
          return;
        }
        throw new Error(data.detail || data.message || 'Failed to generate strategy');
      }

      setResult(data);
      if (data && data.status === 'ok' && data.id) {
        // Fix 1: Route to review page with ID instead of using localStorage
        window.location.href = `/strategy/review?id=${data.id}`;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitClarifications = async (blockerAnswers: Record<string, string>) => {
    // Fix 6: Cap clarification retries
    if (clarificationCount >= MAX_CLARIFICATION_RETRIES) {
      setError(
        `Maximum clarification retries (${MAX_CLARIFICATION_RETRIES}) reached. ` +
        `Please simplify your strategy prompt and try again.`
      );
      return;
    }

    setLoading(true);
    setError(null);

    let augmented = currentStrategyText;
    const blockers = result?.blockers || [];

    blockers.forEach((b) => {
      const answer = blockerAnswers[b.question]?.trim();
      if (answer) {
        augmented += `\n\nClarification regarding '${b.question}': ${answer}`;
      }
    });

    // Fix 6: Check augmented prompt length
    if (augmented.length > MAX_PROMPT_LENGTH) {
      setError(`Augmented prompt exceeds maximum length of ${MAX_PROMPT_LENGTH.toLocaleString()} characters. Please shorten your answers.`);
      setLoading(false);
      return;
    }

    setCurrentStrategyText(augmented);
    setClarificationCount(prev => prev + 1);

    try {
      // Fix 1: Route through server-side proxy
      const response = await fetch('/api/proxy/strategy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: strategyName.trim() || undefined,
          tag: strategyTag.trim() || undefined,
          description: strategyDescription.trim() || undefined,
          prompt: augmented,
          market_type: isEquity ? 'equity' : 'futures',
          execution_context: executionContext
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Failed to generate strategy');
      }

      setResult(data);
      if (data && data.status === 'ok') {
        localStorage.setItem('last_compiled_strategy', JSON.stringify({
          canonical_json: data.canonical_json,
          ast_json: data.ast_json,
          execution_context: executionContext
        }));
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitSemanticResolutions = async (semanticResolutions: Record<string, string>, customSemanticInputs: Record<string, string>) => {
    // Fix 6: Cap clarification retries
    if (clarificationCount >= MAX_CLARIFICATION_RETRIES) {
      setError(
        `Maximum clarification retries (${MAX_CLARIFICATION_RETRIES}) reached. ` +
        `Please simplify your strategy prompt and try again.`
      );
      return;
    }

    setLoading(true);
    setError(null);
    setClarificationCount(prev => prev + 1);

    const approvalItems = result?.approval_items || [];
    const resolutions = approvalItems.map((item) => {
      const chosen = semanticResolutions[item.source] || item.candidates[0];
      const finalResolution = chosen === '__custom__'
        ? customSemanticInputs[item.source]?.trim() || item.candidates[0]
        : chosen;
      return {
        source: item.source,
        resolution: finalResolution,
      };
    });

    try {
      // Fix 1: Route through server-side proxy
      const response = await fetch('/api/proxy/strategy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: strategyName.trim() || undefined,
          tag: strategyTag.trim() || undefined,
          description: strategyDescription.trim() || undefined,
          prompt: currentStrategyText,
          semantic_resolutions: resolutions,
          market_type: isEquity ? 'equity' : 'futures',
          execution_context: executionContext,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        if (data.detail && typeof data.detail === 'object' && Array.isArray(data.detail.messages)) {
          setError(data.detail.messages);
          setLoading(false);
          return;
        }
        throw new Error(data.detail || data.message || 'Failed to generate strategy');
      }

      setResult(data);
      if (data && data.status === 'ok' && data.id) {
        // Fix 1: Route to review page with ID instead of using localStorage
        window.location.href = `/strategy/review?id=${data.id}`;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="col-span-1 lg:col-span-8 flex flex-col relative gap-6">
      <div className="flex-1 flex flex-col p-5 lg:p-6 rounded-2xl bg-surface border border-border shadow-sm text-foreground h-full">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 shrink-0 gap-4">
          <div className="flex items-center gap-5">
            <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600">
              <Wand2 className="text-2xl" size={24} />
            </div>
            <div>
              <h2 className="text-xl font-bold font-display tracking-tight">Natural Language Editor</h2>
              <p className="text-sm text-muted">Describe your strategy logic in plain English.</p>
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col space-y-6 relative mt-6">
          {(!result || result.status !== 'ok') && (
            <>
              <div className="flex flex-col flex-1 min-h-[200px]">
            <label className="text-xs font-bold uppercase tracking-wider text-muted mb-3 shrink-0 block">Entry Condition</label>
            <textarea
              value={entryCondition}
              onChange={(e) => setEntryCondition(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  if (isContextValid && !loading && !isOverLimit) {
                    handleGenerateStrategy();
                  }
                }
              }}
              disabled={loading || !isContextValid}
              maxLength={MAX_PROMPT_LENGTH}
              className="w-full h-full p-4 md:p-5 rounded-xl border border-border bg-surface text-lg resize-none transition-soft focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100 outline-none placeholder:text-muted"
              placeholder={
                !isContextValid
                  ? "Please fill all execution context parameters on the left first..."
                  : "e.g. Buy when RSI crosses above 30 and EMA20 is above EMA50"
              }
            />
          </div>

          <div className="flex flex-col flex-1 min-h-[200px]">
            <label className="text-xs font-bold uppercase tracking-wider text-muted mb-3 shrink-0 block">Exit Condition</label>
            <textarea
              value={exitCondition}
              onChange={(e) => setExitCondition(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  if (isContextValid && !loading && !isOverLimit) {
                    handleGenerateStrategy();
                  }
                }
              }}
              disabled={loading || !isContextValid}
              maxLength={MAX_PROMPT_LENGTH}
              className="w-full h-full p-4 md:p-5 rounded-xl border border-border bg-surface text-lg resize-none transition-soft focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100 outline-none placeholder:text-muted"
              placeholder={
                !isContextValid
                  ? "Please fill all execution context parameters on the left first..."
                  : "e.g. Exit when RSI exceeds 70\n(Press Ctrl+Enter to generate)"
              }
            />
          </div>

          {/* Fix 6: Character counter */}
          {isContextValid && (
            <div className="mt-4 flex flex-col md:flex-row items-center justify-between gap-4 shrink-0">
              <div className="flex flex-col gap-1">
                <span className={`text-sm font-medium ${
                  isOverLimit
                    ? 'text-red-600 font-bold'
                    : remaining < 500
                      ? 'text-amber-600 font-semibold'
                      : 'text-muted'
                }`}>
                  {content.length.toLocaleString()} / {MAX_PROMPT_LENGTH.toLocaleString()} characters
                  {remaining < 500 && remaining >= 0 && ` (${remaining} remaining)`}
                  {isOverLimit && ` — ${Math.abs(remaining)} over limit`}
                </span>
                {clarificationCount > 0 && (
                  <span className="text-xs text-muted">
                    Retries: {clarificationCount}/{MAX_CLARIFICATION_RETRIES}
                  </span>
                )}
              </div>

              <button
                onClick={handleGenerateStrategy}
                disabled={loading || isOverLimit}
                className="w-full md:w-auto px-8 py-3 rounded-xl bg-indigo-600 text-white font-bold shadow-sm transition-soft hover:bg-indigo-700 active:scale-95 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading && !result ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    Generate Strategy
                    <Sparkles className="text-lg" size={20} />
                  </>
                )}
              </button>
            </div>
          )}

          {!isContextValid && (
            <div className="absolute inset-0 bg-surface/80 backdrop-blur-[2px] flex flex-col items-center justify-center p-6 text-center z-10 transition-all duration-300 rounded-[32px]">
              <div className="w-16 h-16 bg-indigo-50 border border-indigo-100 text-indigo-600 rounded-2xl flex items-center justify-center mb-4">
                <Info size={28} />
              </div>
              <h3 className="text-lg font-bold text-foreground">Unlock Natural Language Editor</h3>
              <p className="text-sm text-muted max-w-sm mt-2">
                Please fill all the deterministic parameters (Capital, Timeframe, Stock, etc.) in the <strong>Chart Settings</strong> panel on the left to start writing your strategy.
              </p>
            </div>
          )}
          </>
          )}
        </div>
      </div>

      {error ? (
        <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-sm text-red-700 shadow-sm flex items-start gap-2">
          <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-red-600" />
          <div className="flex-1">
            {Array.isArray(error) ? (
              <ul className="list-disc pl-4 space-y-1">
                {error.map((err, i) => <li key={i}>{err}</li>)}
              </ul>
            ) : (
              <div>{error}</div>
            )}
          </div>
        </div>
      ) : null}

      {/* STAGE 1 & 2: Modal */}
      <AIClarificationModal
        isOpen={!!result && (result.status === 'blocked' || result.status === 'semantic_approval')}
        onClose={() => setResult(null)}
        result={result}
        clarificationCount={clarificationCount}
        loading={loading}
        onSubmitClarifications={handleSubmitClarifications}
        onSubmitSemanticResolutions={handleSubmitSemanticResolutions}
      />

      {/* STAGE 3: Successful compiled outputs */}
      {result && result.status === 'ok' ? (
        <div className="flex-1 flex flex-col animate-fade-in space-y-6 mt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-emerald-50 border border-emerald-100 text-emerald-600 rounded-xl flex items-center justify-center">
                <CheckCircle size={24} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-emerald-500">Strategy Successfully Compiled!</h3>
                <p className="text-sm font-semibold text-foreground mt-0.5">Your strategy logic has been parsed into our engine.</p>
              </div>
            </div>
            <div className="flex gap-4">
              <button
                onClick={() => setResult(null)}
                className="px-6 py-2.5 rounded-xl border border-border bg-surface shadow-sm font-bold transition-soft hover:bg-background text-foreground"
              >
                Back to Editor
              </button>
              <button
                onClick={() => setShowConfigModal(true)}
                className="px-6 py-2.5 rounded-xl bg-emerald-600 text-white font-bold shadow-sm transition-soft hover:bg-emerald-700 active:scale-95"
              >
                Configure & Run Backtest
              </button>
            </div>
          </div>
          
          <div className="flex-1 min-h-0 overflow-y-auto pr-2 custom-scrollbar">
            <StrategySummary
              canonicalJson={result.canonical_json}
              executionContext={executionContext}
            />
          </div>
        </div>
      ) : null}

      {showConfigModal && result?.ast_json && result?.canonical_json && (
        <BacktestConfigModal
          ast={result.ast_json}
          canonical={result.canonical_json}
          executionContext={executionContext}
          onClose={() => setShowConfigModal(false)}
        />
      )}
    </section>
  );
}
