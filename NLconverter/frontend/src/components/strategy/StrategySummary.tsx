"use client";
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { BrainCircuit, Play, TrendingUp, Compass } from 'lucide-react';

interface StrategySummaryProps {
  canonicalJson?: any;
  executionContext?: any;
}

export default function StrategySummary({ canonicalJson, executionContext }: StrategySummaryProps) {
  const [data, setData] = useState<{ canonical: any; context: any }>({
    canonical: canonicalJson || null,
    context: executionContext || null
  });

  useEffect(() => {
    // If props are passed, use them
    if (canonicalJson || executionContext) {
      setData({
        canonical: canonicalJson || undefined,
        context: executionContext || undefined
      });
    }
  }, [canonicalJson, executionContext]);

  const { canonical, context } = data;
  if (!canonical) return null;
  const indicators = canonical?.signals?.indicators || [];

  const formatOperand = (operand: any): string => {
    if (!operand) return '';
    if (operand.type === 'market_data' || operand.type === 'market') {
      const lb = operand.lookback || 0;
      const lbStr = lb > 0 ? ` (t-${lb})` : '';
      const name = operand.data_type
        ? operand.data_type.charAt(0).toUpperCase() + operand.data_type.slice(1).toLowerCase()
        : 'Price';
      return `${name}${lbStr}`;
    }
    if (operand.type === 'indicator') {
      const ind = indicators.find((i: any) => i.id === operand.indicator_id);
      if (ind) {
        const paramParts: string[] = [];
        if (ind.params) {
          Object.entries(ind.params).forEach(([key, val]) => {
            const cleanKey = key.replace(/_/g, ' ');
            paramParts.push(`${cleanKey}: ${val}`);
          });
        }
        const paramStr = paramParts.length > 0 ? ` (${paramParts.join(', ')})` : '';
        const propStr = operand.property && operand.property !== 'value'
          ? `'s ${operand.property.replace(/_/g, ' ')}`
          : '';
        const name = ind.name
          ? ind.name.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c: string) => c.toUpperCase())
          : 'Indicator';
        return `${name}${propStr}${paramStr}`;
      }
      return operand.indicator_id || 'Indicator';
    }
    if (operand.type === 'constant' || operand.value !== undefined) {
      return String(operand.value);
    }
    return JSON.stringify(operand);
  };

  const formatOperator = (opType: string): string => {
    switch (opType) {
      case 'GREATER_THAN': return 'is greater than (>)';
      case 'LESS_THAN': return 'is less than (<)';
      case 'GREATER_THAN_EQUAL': return 'is greater than or equal to (>=)';
      case 'LESS_THAN_EQUAL': return 'is less than or equal to (<=)';
      case 'EQUAL': return 'is equal to (==)';
      case 'NOT_EQUAL': return 'is not equal to (!=)';
      case 'CROSSES_ABOVE': return 'crosses above';
      case 'CROSSES_BELOW': return 'crosses below';
      default: return opType ? opType.replace(/_/g, ' ').toLowerCase() : 'is';
    }
  };

  const formatCondition = (cond: any): string => {
    if (cond.type === 'AND' || cond.type === 'OR' || cond.operator === 'AND' || cond.operator === 'OR') {
      const children = cond.children || cond.operands || [];
      const joinStr = cond.type === 'AND' || cond.operator === 'AND' ? ' AND ' : ' OR ';
      const formattedChildren = children.map((c: any) => formatCondition(c)).filter((s: string) => s !== 'Unknown condition');
      if (formattedChildren.length === 0) return 'Unknown condition';
      if (formattedChildren.length === 1) return formattedChildren[0];
      return `(${formattedChildren.join(joinStr)})`;
    }

    const op1 = formatOperand(cond.operand_1);
    const op2 = formatOperand(cond.operand_2);
    const op = formatOperator(cond.type || cond.operator);
    if (!op1 && !op2) return 'Unknown condition';
    return `${op1} ${op} ${op2}`;
  };

  // Generate Entry and Exit Conditions list
  const entryConditions: string[] = [];
  const exitConditions: string[] = [];
  
  if (canonical?.operation && Array.isArray(canonical.operation)) {
    canonical.operation.forEach((op: any, index: number) => {
      const prefix = canonical.operation.length > 1 ? `[Leg ${index + 1}] ` : '';
      const entries = op.entry || [];
      entries.forEach((cond: any) => {
        entryConditions.push(prefix + formatCondition(cond));
      });
      const exits = op.exit || [];
      exits.forEach((cond: any) => {
        exitConditions.push(prefix + formatCondition(cond));
      });
    });
  } else if (canonical?.operation && !Array.isArray(canonical.operation)) {
    // Handle single operation (non-array) case
    const op = canonical.operation;
    const entries = op.entry || [];
    entries.forEach((cond: any) => {
      entryConditions.push(formatCondition(cond));
    });
    const exits = op.exit || [];
    exits.forEach((cond: any) => {
      exitConditions.push(formatCondition(cond));
    });
  }


  // Generate Risk & Context details list
  const riskList: string[] = [];
  const risk = canonical?.risk;
  if (risk) {
    if (risk.stop_loss && risk.stop_loss.value !== null && risk.stop_loss.value !== undefined) {
      const val = risk.stop_loss.value;
      const type = risk.stop_loss.type || 'percentage';
      riskList.push(`Stop Loss: ${val}${type === 'percentage' ? '%' : ` ${type}`}`);
    }
    if (risk.take_profit && risk.take_profit.value !== null && risk.take_profit.value !== undefined) {
      const val = risk.take_profit.value;
      const type = risk.take_profit.type || 'percentage';
      riskList.push(`Take Profit: ${val}${type === 'percentage' ? '%' : ` ${type}`}`);
    }
    if (risk.risk_reward && risk.risk_reward.value !== null && risk.risk_reward.value !== undefined) {
      riskList.push(`Risk Reward Ratio: 1:${risk.risk_reward.value}`);
    } else if (risk.risk_reward && risk.risk_reward.ratio !== null && risk.risk_reward.ratio !== undefined) {
      riskList.push(`Risk Reward Ratio: 1:${risk.risk_reward.ratio}`);
    }
    if (risk.trailing_stop && risk.trailing_stop.value !== null && risk.trailing_stop.value !== undefined) {
      const val = risk.trailing_stop.value;
      const type = risk.trailing_stop.type || 'percentage';
      riskList.push(`Trailing Stop: ${val}${type === 'percentage' ? '%' : ` ${type}`}`);
    }
  }

  if (context) {
    if (context.position_side) {
      riskList.push(`Position Side: ${context.position_side}`);
    }
    if (context.timeframe) {
      riskList.push(`Timeframe: ${context.timeframe}`);
    }
    if (context.universe) {
      const uni = context.universe;
      riskList.push(`Universe: ${uni.index || 'NIFTY_50'} (${uni.exchange || 'NSE'})`);
    }
    if (context.stocks && context.stocks.length > 0) {
      const displayStocks = context.stocks.length > 5 
        ? `${context.stocks.slice(0, 5).join(', ')} +${context.stocks.length - 5} more` 
        : context.stocks.join(', ');
      riskList.push(`Instruments: ${displayStocks}`);
    }
  }

  return (
    <section id="what-i-understood" className="w-full">
      <div className="bg-surface border border-border rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center">
              <BrainCircuit className="text-xl" size={20} />
            </div>
            <h2 className="text-lg font-bold text-foreground">Summary</h2>
          </div>
          <Link id="edit-strategy-btn" href="/strategy" className="text-xs font-bold text-blue-600 hover:underline">
            Edit Strategy
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
          <div className="space-y-4">
            <div>
              <div className="flex items-center gap-1.5 mb-3">
                <TrendingUp className="text-emerald-500 shrink-0" size={16} />
                <h3 className="text-xs font-bold text-blue-600 uppercase tracking-widest">Entry Conditions</h3>
              </div>
              {entryConditions.length > 0 ? (
                <ul className="space-y-2 text-foreground font-medium">
                  {entryConditions.map((cond, idx) => (
                    <li key={idx} className="flex items-start gap-2 leading-relaxed">
                      <span className="text-blue-400 shrink-0 mt-1">•</span>
                      <span>{cond}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-muted italic">No entry conditions specified.</p>
              )}
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <div className="flex items-center gap-1.5 mb-3">
                <Play className="text-rose-500 rotate-90 shrink-0" size={16} />
                <h3 className="text-xs font-bold text-blue-600 uppercase tracking-widest">Exit Conditions</h3>
              </div>
              {exitConditions.length > 0 ? (
                <ul className="space-y-2 text-foreground font-medium">
                  {exitConditions.map((cond, idx) => (
                    <li key={idx} className="flex items-start gap-2 leading-relaxed">
                      <span className="text-blue-400 shrink-0 mt-1">•</span>
                      <span>{cond}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-muted italic">No exit conditions specified.</p>
              )}
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <div className="flex items-center gap-1.5 mb-3">
                <Compass className="text-blue-500 shrink-0" size={16} />
                <h3 className="text-xs font-bold text-blue-600 uppercase tracking-widest">Risk & Execution</h3>
              </div>
              {riskList.length > 0 ? (
                <ul className="space-y-2 text-foreground font-medium">
                  {riskList.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2 leading-relaxed">
                      <span className="text-blue-400 shrink-0 mt-1">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-muted italic">No custom risk parameters defined.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
