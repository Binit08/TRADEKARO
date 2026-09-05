import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface GaugeProps {
  value: number;
  min?: number;
  max?: number;
  unit?: string;
  color?: string;
}

export default function Gauge({ value, min = 0, max = 100, unit = '', color = '#10B981' }: GaugeProps) {
  // Normalize value between min and max
  const normalizedValue = Math.min(Math.max(value, min), max);
  const percentage = ((normalizedValue - min) / (max - min)) * 100;
  
  const data = [
    { name: 'Value', value: percentage },
    { name: 'Empty', value: 100 - percentage }
  ];

  const cx = "50%";
  const cy = "75%";
  const iR = "60%";
  const oR = "80%";

  return (
    <div className="flex flex-col items-center justify-center relative h-32 w-full">
      <div className="absolute top-0 left-0 w-full h-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx={cx}
              cy={cy}
              startAngle={180}
              endAngle={0}
              innerRadius={iR}
              outerRadius={oR}
              stroke="none"
              dataKey="value"
            >
              <Cell key="cell-0" fill={color} />
              <Cell key="cell-1" fill="#E2E8F0" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="absolute bottom-2 flex flex-col items-center">
        <span className="text-2xl font-black font-industrial text-foreground">{value.toFixed(1)}{unit}</span>
      </div>
    </div>
  );
}
