"use client";
import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { X, TrendingUp, BarChart2, LineChart } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface CreateStrategyWizardModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CreateStrategyWizardModal({ isOpen, onClose }: CreateStrategyWizardModalProps) {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [strategyType, setStrategyType] = useState<'equity' | 'future' | null>(null);
  
  // Step 2 Form State
  const [name, setName] = useState('');
  const [category, setCategory] = useState('Equity Intraday');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [description, setDescription] = useState('');

  if (!isOpen) return null;

  const handleNext = () => {
    if (step === 1 && strategyType) {
      setStep(2);
      // Auto-set default category based on type
      if (strategyType === 'equity') setCategory('Equity Intraday');
      if (strategyType === 'future') setCategory('Futures Intraday');
    }
  };

  const handleSave = () => {
    if (!name.trim()) {
      alert("Please enter a name for the strategy.");
      return;
    }
    // Save metadata to local storage so /strategy page can pick it up
    localStorage.setItem('strategy_metadata', JSON.stringify({
      name,
      category,
      tags,
      description,
      type: strategyType
    }));
    
    onClose();
    // Navigate to strategy builder page
    router.push(`/strategy?type=${strategyType}`);
  };

  const handleAddTag = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      if (tags.length < 5 && !tags.includes(tagInput.trim())) {
        setTags([...tags, tagInput.trim()]);
      }
      setTagInput('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter(t => t !== tagToRemove));
  };

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      ></div>

      {/* Modal Content */}
      <div className="relative bg-background w-full max-w-4xl rounded-2xl shadow-2xl flex flex-col overflow-hidden max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface z-10">
          <h2 className="text-xl font-bold text-foreground">
            {step === 1 ? 'Step 1: What do you want to create?' : 'Step 2: Save Strategy'}
          </h2>
          <button 
            onClick={onClose}
            className="p-2 text-muted hover:text-foreground hover:bg-background rounded-full transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 md:p-8">
          {step === 1 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Equity Card */}
              <div 
                onClick={() => setStrategyType('equity')}
                className={`relative bg-surface border-2 rounded-xl p-6 cursor-pointer transition-all duration-300 hover:shadow-lg group ${
                  strategyType === 'equity' ? 'border-accent-primary shadow-md scale-[1.02] ring-4 ring-accent-primary/10' : 'border-border hover:border-accent-primary/50'
                }`}
              >
                <div className={`h-48 rounded-lg mb-6 flex items-center justify-center relative overflow-hidden transition-colors ${strategyType === 'equity' ? 'bg-accent-secondary' : 'bg-background group-hover:bg-accent-secondary/50'}`}>
                   <div className="flex flex-col items-center justify-center text-muted gap-3">
                     <LineChart size={48} className={strategyType === 'equity' ? 'text-accent-primary' : 'text-muted group-hover:text-accent-primary'} />
                     <span className={`text-2xl font-semibold tracking-wide ${strategyType === 'equity' ? 'text-accent-primary' : 'text-foreground'}`}>Equity</span>
                   </div>
                </div>
                <h3 className={`text-xl font-bold mb-2 ${strategyType === 'equity' ? 'text-accent-primary' : 'text-foreground'}`}>
                  Equity
                </h3>
                <p className="text-muted text-sm leading-relaxed">
                  Equity trading style, can do swing trading, day trading, and position trading.
                </p>
              </div>

              {/* Futures Card */}
              <div 
                onClick={() => setStrategyType('future')}
                className={`relative bg-surface border-2 rounded-xl p-6 cursor-pointer transition-all duration-300 hover:shadow-lg group ${
                  strategyType === 'future' ? 'border-accent-primary shadow-md scale-[1.02] ring-4 ring-accent-primary/10' : 'border-border hover:border-accent-primary/50'
                }`}
              >
                <div className={`h-48 rounded-lg mb-6 flex items-center justify-center relative overflow-hidden transition-colors ${strategyType === 'future' ? 'bg-accent-secondary' : 'bg-background group-hover:bg-accent-secondary/50'}`}>
                   <div className="flex flex-col items-center justify-center text-muted gap-3">
                     <TrendingUp size={48} className={strategyType === 'future' ? 'text-accent-primary' : 'text-muted group-hover:text-accent-primary'} />
                     <span className={`text-2xl font-semibold tracking-wide ${strategyType === 'future' ? 'text-accent-primary' : 'text-foreground'}`}>Futures</span>
                   </div>
                </div>
                <h3 className={`text-xl font-bold mb-2 ${strategyType === 'future' ? 'text-accent-primary' : 'text-foreground'}`}>
                  Futures
                </h3>
                <p className="text-muted text-sm leading-relaxed">
                  Futures trading style, leverage derivatives to trade based on underlying asset price movements.
                </p>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="max-w-2xl mx-auto space-y-6 bg-surface p-6 rounded-xl border border-border shadow-sm">
              
              {/* Name */}
              <div>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter a name to save"
                  className="w-full px-4 py-3 rounded-lg border border-border focus:outline-none focus:ring-4 focus:ring-accent-primary/20 focus:border-accent-primary transition-all text-foreground placeholder-muted font-medium bg-surface shadow-sm"
                />
              </div>

              {/* Category */}
              <div className="flex items-center gap-4 pt-2">
                <span className="text-sm font-semibold text-foreground min-w-[80px]">Category</span>
                <div className="flex items-center gap-3">
                  {strategyType === 'equity' ? (
                    <>
                      <button 
                        onClick={() => setCategory('Equity Intraday')}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-2 border ${category === 'Equity Intraday' ? 'bg-accent-secondary border-accent-primary/30 text-accent-primary shadow-sm' : 'bg-background border-border text-muted hover:bg-surface'}`}
                      >
                        <span className={category === 'Equity Intraday' ? 'text-accent-primary' : 'text-muted'}>⏱</span> Equity Intraday
                      </button>
                      <button 
                        onClick={() => setCategory('Equity Swing')}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-2 border ${category === 'Equity Swing' ? 'bg-accent-secondary border-accent-primary/30 text-accent-primary shadow-sm' : 'bg-background border-border text-muted hover:bg-surface'}`}
                      >
                        <BarChart2 size={14} className={category === 'Equity Swing' ? 'text-accent-primary' : 'text-muted'} /> Equity Swing
                      </button>
                    </>
                  ) : (
                    <>
                      <button 
                        onClick={() => setCategory('Futures Intraday')}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-2 border ${category === 'Futures Intraday' ? 'bg-accent-secondary border-accent-primary/30 text-accent-primary shadow-sm' : 'bg-background border-border text-muted hover:bg-surface'}`}
                      >
                        <span className={category === 'Futures Intraday' ? 'text-accent-primary' : 'text-muted'}>⏱</span> Futures Intraday
                      </button>
                      <button 
                        onClick={() => setCategory('Futures Swing')}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-2 border ${category === 'Futures Swing' ? 'bg-accent-secondary border-accent-primary/30 text-accent-primary shadow-sm' : 'bg-background border-border text-muted hover:bg-surface'}`}
                      >
                        <BarChart2 size={14} className={category === 'Futures Swing' ? 'text-accent-primary' : 'text-muted'} /> Futures Swing
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Tags */}
              <div className="pt-2">
                <div className="flex items-start gap-4">
                  <span className="text-sm font-semibold text-foreground min-w-[80px] mt-3">Tags</span>
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      {tags.map(tag => (
                        <span key={tag} className="flex items-center gap-1 px-2.5 py-1 bg-accent-secondary text-accent-primary rounded-md text-sm font-medium border border-accent-primary/20">
                          {tag}
                          <button onClick={() => removeTag(tag)} className="text-accent-primary/70 hover:text-accent-primary"><X size={14} /></button>
                        </span>
                      ))}
                    </div>
                    <div className="relative">
                      <input
                        type="text"
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        onKeyDown={handleAddTag}
                        placeholder="Enter a tag"
                        disabled={tags.length >= 5}
                        className="w-full px-4 py-3 rounded-lg border border-border focus:outline-none focus:ring-4 focus:ring-accent-primary/20 focus:border-accent-primary transition-all text-foreground disabled:bg-background disabled:cursor-not-allowed bg-surface shadow-sm"
                      />
                      <div className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-medium text-muted">
                        {tags.length}/5
                      </div>
                    </div>
                    <p className="text-[11px] text-muted mt-1.5 text-right">Press Enter to add the Tag*</p>
                  </div>
                </div>
              </div>

              {/* Description */}
              <div className="pt-2">
                <p className="text-sm font-semibold text-foreground mb-2">Description</p>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Enter a description to save"
                  className="w-full px-4 py-3 rounded-lg border border-border focus:outline-none focus:ring-4 focus:ring-accent-primary/20 focus:border-accent-primary transition-all text-foreground placeholder-muted resize-none h-32 bg-surface shadow-sm"
                />
              </div>

            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-border bg-surface">
          <div className="flex items-center gap-2">
            <div className={`w-8 h-1 rounded-full transition-colors ${step === 1 ? 'bg-accent-primary' : 'bg-accent-primary/30'}`}></div>
            <div className={`w-8 h-1 rounded-full transition-colors ${step === 2 ? 'bg-accent-primary' : 'bg-border'}`}></div>
          </div>
          
          <div className="flex items-center gap-3">
            {step === 2 && (
              <button 
                onClick={() => setStep(1)}
                className="px-6 py-2.5 rounded-lg text-foreground font-medium hover:bg-background transition-colors border border-border hover:border-muted shadow-sm"
              >
                Back
              </button>
            )}
            <button 
              onClick={step === 1 ? handleNext : handleSave}
              disabled={step === 1 && !strategyType}
              className="px-8 py-2.5 bg-accent-primary text-white rounded-lg font-medium hover:bg-blue-700 transition-all shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {step === 1 ? 'Next' : 'Save'}
            </button>
          </div>
        </div>

      </div>
    </div>,
    document.body
  );
}
