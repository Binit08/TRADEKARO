import React, { useState, useEffect } from 'react';
import { AlertTriangle, HelpCircle, X } from 'lucide-react';
import type { StrategyResult } from './NaturalLanguageEditor';

interface AIClarificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  result: StrategyResult | null;
  clarificationCount: number;
  loading: boolean;
  onSubmitClarifications: (answers: Record<string, string>) => void;
  onSubmitSemanticResolutions: (resolutions: Record<string, string>, customInputs: Record<string, string>) => void;
}

const MAX_CLARIFICATION_RETRIES = 5;

export const AIClarificationModal: React.FC<AIClarificationModalProps> = ({
  isOpen,
  onClose,
  result,
  clarificationCount,
  loading,
  onSubmitClarifications,
  onSubmitSemanticResolutions,
}) => {
  const [blockerAnswers, setBlockerAnswers] = useState<Record<string, string>>({});
  const [semanticResolutions, setSemanticResolutions] = useState<Record<string, string>>({});
  const [customSemanticInputs, setCustomSemanticInputs] = useState<Record<string, string>>({});

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setBlockerAnswers({});
      setSemanticResolutions({});
      setCustomSemanticInputs({});
    }
  }, [isOpen, result]);

  if (!isOpen || !result) return null;

  const handleClarificationSubmit = () => {
    onSubmitClarifications(blockerAnswers);
  };

  const handleSemanticSubmit = () => {
    onSubmitSemanticResolutions(semanticResolutions, customSemanticInputs);
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-8">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-gray-900/50 backdrop-blur-sm transition-opacity"
        onClick={!loading ? onClose : undefined}
      />
      
      {/* Modal Container */}
      <div className="relative w-full max-w-4xl max-h-full flex flex-col p-6 lg:p-8 rounded-xl bg-surface text-foreground shadow-xl border border-border">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          disabled={loading}
          className="absolute top-6 right-6 lg:top-8 lg:right-8 w-10 h-10 rounded-lg flex items-center justify-center text-muted hover:text-muted hover:bg-surface transition-colors disabled:opacity-50"
        >
          <X size={24} />
        </button>

        <div className="overflow-y-auto custom-scrollbar pr-4 flex-1">
          {/* STAGE 1: Blocker Clarification Form */}
          {result.status === 'blocked' && result.blockers && result.blockers.length > 0 ? (
            <div className="flex flex-col space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center shrink-0">
                  <AlertTriangle size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-foreground">Clarification Required</h3>
                  <p className="text-sm text-muted mt-1">
                    The AI engine needs additional details before compiling this strategy.
                    {clarificationCount > 0 && (
                      <span className="ml-1 font-medium text-foreground">
                        (Attempt {clarificationCount}/{MAX_CLARIFICATION_RETRIES})
                      </span>
                    )}
                  </p>
                </div>
              </div>

              <div className="space-y-6 mt-4">
                {result.blockers.map((b: { reason: string; question: string }, idx: number) => (
                  <div key={idx} className="flex flex-col gap-3">
                    <div>
                      <span className="text-xs font-semibold uppercase text-indigo-600 bg-indigo-50 px-2 py-1 rounded-md inline-block">
                        Reason: {b.reason}
                      </span>
                      <h4 className="text-base font-medium text-foreground mt-2">{b.question}</h4>
                    </div>
                    <textarea
                      rows={3}
                      value={blockerAnswers[b.question] || ''}
                      onChange={(e) => setBlockerAnswers({ ...blockerAnswers, [b.question]: e.target.value })}
                      placeholder="Provide clarification details here..."
                      className="w-full text-sm p-4 rounded-lg border border-border bg-surface focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none placeholder:text-muted text-foreground resize-none"
                    />
                  </div>
                ))}
              </div>

              <div className="flex flex-col sm:flex-row sm:justify-end gap-3 pt-6 mt-auto">
                <button
                  onClick={onClose}
                  className="px-5 py-2.5 rounded-lg font-medium text-foreground bg-surface border border-border hover:bg-background transition-colors"
                >
                  Cancel & Edit Prompt
                </button>
                <button
                  onClick={handleClarificationSubmit}
                  disabled={loading || clarificationCount >= MAX_CLARIFICATION_RETRIES}
                  className="px-6 py-2.5 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Submitting...' : 'Submit Answers & Re-evaluate'}
                </button>
              </div>
            </div>
          ) : null}

          {/* STAGE 2: Semantic Resolver Form */}
          {result.status === 'semantic_approval' && result.approval_items && result.approval_items.length > 0 ? (
            <div className="flex flex-col space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center shrink-0">
                  <HelpCircle size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-foreground">Resolve Ambiguous Terms</h3>
                  <p className="text-sm text-muted mt-1">
                    Confirm or override the AI interpretations for these trading terms.
                    {clarificationCount > 0 && (
                      <span className="ml-1 font-medium text-foreground">
                        (Attempt {clarificationCount}/{MAX_CLARIFICATION_RETRIES})
                      </span>
                    )}
                  </p>
                </div>
              </div>

              <div className="space-y-8 mt-4">
                {result.approval_items.map((item: { source: string; candidates: string[]; confidence: number }, idx: number) => {
                  const selectedValue = semanticResolutions[item.source] || item.candidates[0];
                  return (
                    <div key={idx} className="flex flex-col gap-4">
                      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                        <div>
                          <span className="text-xs font-semibold uppercase text-indigo-600 bg-indigo-50 px-2 py-1 rounded-md inline-block">
                            Ambiguous term: &quot;{item.source}&quot;
                          </span>
                          <p className="text-sm font-medium text-foreground mt-2">Select the correct matching parameter configuration.</p>
                        </div>
                        <span className="text-xs font-medium text-teal-700 bg-teal-50 px-3 py-1 rounded-full border border-teal-200 whitespace-nowrap self-start">
                          Confidence: {Math.round(item.confidence * 100)}%
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="relative border border-border rounded-lg bg-surface flex focus-within:ring-1 focus-within:ring-indigo-500 focus-within:border-indigo-500">
                          <select
                            value={selectedValue}
                            onChange={(e) => setSemanticResolutions({ ...semanticResolutions, [item.source]: e.target.value })}
                            className="w-full bg-transparent px-4 py-3 text-sm font-medium text-foreground appearance-none focus:outline-none"
                          >
                            {item.candidates.map((cand: string, candIdx: number) => (
                              <option key={candIdx} value={cand}>
                                {cand} {candIdx === 0 ? '[Default]' : ''}
                              </option>
                            ))}
                            <option value="__custom__">Write my own...</option>
                          </select>
                        </div>

                        {selectedValue === '__custom__' ? (
                          <input
                            type="text"
                            placeholder="Enter custom resolution (e.g. RSI > 50)"
                            value={customSemanticInputs[item.source] || ''}
                            onChange={(e) => setCustomSemanticInputs({ ...customSemanticInputs, [item.source]: e.target.value })}
                            className="w-full px-4 py-3 text-sm font-medium text-foreground bg-surface border border-border rounded-lg focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none placeholder:text-muted"
                          />
                        ) : null}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="flex flex-col sm:flex-row sm:justify-end gap-3 pt-6 mt-auto">
                <button
                  onClick={onClose}
                  className="px-5 py-2.5 rounded-lg font-medium text-foreground bg-surface border border-border hover:bg-background transition-colors"
                >
                  Cancel & Edit Prompt
                </button>
                <button
                  onClick={handleSemanticSubmit}
                  disabled={loading || clarificationCount >= MAX_CLARIFICATION_RETRIES}
                  className="px-6 py-2.5 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Submitting...' : 'Confirm Selections & Compile'}
                </button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};
