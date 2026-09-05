import React from 'react';
import { Check } from 'lucide-react';

export default function ValidationStatus() {
  return (
    <section id="validation-status" className="grid grid-cols-1 md:grid-cols-3 gap-4 pb-12">
      <div className="validation-card">
        <div className="w-10 h-10 bg-emerald-500 text-white rounded-2xl flex items-center justify-center shadow-md">
          <Check className="text-lg" size={20} />
        </div>
        <p className="text-sm font-bold text-emerald-800">No blockers found</p>
      </div>
      <div className="validation-card">
        <div className="w-10 h-10 bg-emerald-500 text-white rounded-2xl flex items-center justify-center shadow-md">
          <Check className="text-lg" size={20} />
        </div>
        <p className="text-sm font-bold text-emerald-800">Strategy can be compiled</p>
      </div>
      <div className="validation-card">
        <div className="w-10 h-10 bg-emerald-500 text-white rounded-2xl flex items-center justify-center shadow-md">
          <Check className="text-lg" size={20} />
        </div>
        <p className="text-sm font-bold text-emerald-800">Ready for backtesting</p>
      </div>
    </section>
  );
}
