"use client";
import React, { useState } from 'react';
import { CheckCircle2 } from 'lucide-react';

interface Option {
  id: string;
  label: string;
}

interface AssumptionBoxProps {
  title: string;
  aiSelectedLabel: string;
  options: Option[];
  name: string;
}

export default function AssumptionBox({ title, aiSelectedLabel, options, name }: AssumptionBoxProps) {
  const [selected, setSelected] = useState<string>(options[0].id);

  return (
    <div className="assumption-box">
      <h4 className="text-2xl font-bold text-foreground mb-8">{title}</h4>
      <div className="flex flex-col items-start gap-4">
        <div className="ai-badge">
          <CheckCircle2 size={24} /> {aiSelectedLabel} (AI Selected)
        </div>
        <div className="radio-group">
          {options.map((opt) => (
            <div className="radio-option" key={opt.id}>
              <input 
                type="radio" 
                id={opt.id} 
                name={name} 
                className="radio-input hidden" 
                checked={selected === opt.id}
                onChange={() => setSelected(opt.id)}
              />
              <label htmlFor={opt.id} className="radio-label">
                <div className="radio-custom-circle">
                  <div className="radio-inner-dot"></div>
                </div>
                <span className="font-semibold">{opt.label}</span>
              </label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
