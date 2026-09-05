"use client";
import React, { useEffect, useState, Suspense } from 'react';
import InnerHeader from '@/components/layout/InnerHeader';
import StrategySummary from '@/components/strategy/StrategySummary';
import AssumptionBox from '@/components/strategy/AssumptionBox';
import ValidationStatus from '@/components/strategy/ValidationStatus';
import BottomBar from '@/components/layout/BottomBar';

import { useSearchParams } from 'next/navigation';
import BacktestConfigModal from '@/components/strategy/BacktestConfigModal';
import Loader from '@/components/ui/Loader';

function ReviewStrategyContent() {
  const searchParams = useSearchParams();
  const id = searchParams.get('id');

  const [strategyData, setStrategyData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showConfigModal, setShowConfigModal] = useState(false);

  useEffect(() => {
    if (!id) {
      setError("No strategy ID provided.");
      setLoading(false);
      return;
    }

    const fetchStrategy = async () => {
      try {
        const response = await fetch(`/api/proxy/strategy/${id}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to fetch strategy");
        setStrategyData(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchStrategy();
  }, [id]);

  const canonical = strategyData?.canonical_json;
  const ast = strategyData?.ast_json;
  const executionContext = strategyData?.execution_context;

  const generateAssumptions = () => {
    if (!canonical) return [];
    
    const assumptions = [];
    
    // Check indicators
    if (canonical.signals?.indicators) {
      canonical.signals.indicators.forEach((ind: any, idx: number) => {
        if (ind.params && ind.params.period) {
          assumptions.push(
            <AssumptionBox 
              key={`ind-${idx}`}
              title={`${ind.name || 'Indicator'} period used:`}
              aiSelectedLabel={ind.params.period.toString()}
              name={`ind-period-${idx}`}
              options={[
                { id: `opt-14-${idx}`, label: ind.params.period.toString() },
                { id: `opt-21-${idx}`, label: '21' },
                { id: `opt-7-${idx}`, label: '7' }
              ]}
            />
          );
        }
      });
    }

    // Check exit quantity
    const exitQty = canonical.operation?.[0]?.exit_quantity;
    if (exitQty !== undefined) {
      assumptions.push(
        <AssumptionBox 
          key="exit-qty"
          title="Exit quantity for positions:"
          aiSelectedLabel={exitQty === 1.0 ? '100%' : `${exitQty * 100}%`}
          name="exit-q"
          options={[
            { id: 'exit-100', label: '100%' },
            { id: 'exit-50', label: '50%' },
            { id: 'exit-25', label: '25%' },
            { id: 'exit-custom', label: 'Custom' },
          ]}
        />
      );
    }
    
    // Add default execution timing
    assumptions.push(
      <AssumptionBox 
        key="exec-timing"
        title="Execution timing:"
        aiSelectedLabel="Candle Close"
        name="exec-t"
        options={[
          { id: 'exec-close', label: 'Candle Close' },
          { id: 'exec-open', label: 'Candle Open' },
          { id: 'exec-intra', label: 'Intrabar' },
          { id: 'exec-custom', label: 'Custom' },
        ]}
      />
    );

    return assumptions;
  };

  const assumptions = generateAssumptions();

  return (
    <div className="min-h-screen bg-background flex flex-col font-sans pb-24">
      <InnerHeader />
      
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 space-y-4">
            <Loader />
            <p className="text-muted text-sm font-medium mt-4">Loading strategy details...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-xl text-center">
            <p className="font-semibold">{error}</p>
          </div>
        ) : (
          <>
            <StrategySummary canonicalJson={canonical} executionContext={executionContext} />
        
        <section id="assumptions-to-review" className="space-y-8">
          <div>
            <h2 className="text-2xl font-bold text-foreground">Assumptions I Had To Make</h2>
            <p className="text-lg text-muted mt-1">Confirm the automated decisions I made to bridge the gaps in your strategy.</p>
          </div>
          
          <div className="space-y-4">
            {assumptions.length > 0 ? assumptions : (
              <p className="text-sm text-muted italic">No major assumptions were required.</p>
            )}
          </div>
          </section>
          
          <ValidationStatus />
          </>
        )}
      </main>
      
      {!loading && !error && strategyData && (
        <BottomBar onConfirm={() => setShowConfigModal(true)} />
      )}

      {showConfigModal && (
        <BacktestConfigModal
          strategyId={strategyData?.id}
          ast={ast}
          canonical={canonical}
          executionContext={executionContext}
          onClose={() => setShowConfigModal(false)}
        />
      )}
    </div>
  );
}

export default function ReviewStrategyPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader />
      </div>
    }>
      <ReviewStrategyContent />
    </Suspense>
  );
}
