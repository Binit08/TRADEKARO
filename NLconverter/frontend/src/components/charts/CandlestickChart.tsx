"use client";
import React, { useEffect, useRef } from 'react';
import { createChart, ColorType, CandlestickSeries, createSeriesMarkers } from 'lightweight-charts';
import { useTheme } from 'next-themes';

interface OHLCCandle {
  time: string | number;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface Trade {
  entry_time: string;
  exit_time?: string;
  side: string;
  qty: number;
  entry_price: number;
  exit_price?: number;
  pnl?: number;
}

interface CandlestickChartProps {
  ohlcData: OHLCCandle[];
  trades: Trade[];
  timeframe: string;
}

export default function CandlestickChart({ ohlcData, trades, timeframe }: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    if (!chartContainerRef.current || ohlcData.length === 0) return;
    
    const isDark = resolvedTheme === 'dark';

    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    const toUnixSeconds = (val: string | number) => {
      if (!val) return null;
      
      let numVal;
      if (typeof val === 'number') {
        numVal = val;
      } else if (typeof val === 'string' && !isNaN(Number(val))) {
        numVal = Number(val);
      }
      
      if (numVal !== undefined) {
        return numVal > 1e11 ? Math.floor(numVal / 1000) : numVal;
      }

      let safeStr = typeof val === 'string' ? val.trim() : String(val).trim();
      if (safeStr.includes(' ')) {
        safeStr = safeStr.replace(' ', 'T');
      }
      
      // If the backend returns naive UTC strings, append Z to force Date to parse it as UTC.
      // This will convert it correctly so that local browsers display it as IST (+5:30) automatically.
      const hasTime = safeStr.includes('T');
      const hasTimezone = safeStr.endsWith('Z') || (hasTime && safeStr.indexOf('+', safeStr.indexOf('T')) !== -1) || (hasTime && safeStr.indexOf('-', safeStr.indexOf('T')) !== -1);
      
      if (hasTime && !hasTimezone) {
        safeStr += 'Z';
      }
      
      return Math.floor(new Date(safeStr).getTime() / 1000);
    };

    // Format OHLC data
    const formattedData = ohlcData.map((d) => {
      return {
        time: toUnixSeconds(d.time) as number,
        open: Number(d.open),
        high: Number(d.high),
        low: Number(d.low),
        close: Number(d.close),
      };
    });

    // Deduplicate and sort OHLC data by time in ascending order to prevent lightweight-charts sorting errors
    formattedData.sort((a, b) => a.time - b.time);
    
    // Filter out duplicates which break lightweight-charts
    const uniqueData = [];
    const seenTimes = new Set();
    for (const d of formattedData) {
      if (!seenTimes.has(d.time)) {
        seenTimes.add(d.time);
        uniqueData.push(d);
      }
    }

    // Helper to format trade entry/exit times to align with candle times
    const formatTime = (timeStr: string) => {
      return toUnixSeconds(timeStr);
    };

    // Format trade execution markers
    const normalizeSide = (s: string) => {
      const upper = s?.toUpperCase() || '';
      if (upper === 'BUY' || upper === 'LONG') return 'LONG';
      if (upper === 'SELL' || upper === 'SHORT') return 'SHORT';
      return upper;
    };

    const markers: any[] = [];
    trades.forEach((trade) => {
      const side = normalizeSide(trade.side);
      const isLong = side === 'LONG';

      // 1. Entry Marker
      const entryTime = formatTime(trade.entry_time);
      if (entryTime) {
        markers.push({
          time: entryTime,
          position: isLong ? 'belowBar' : 'aboveBar',
          color: isLong ? '#10b981' : '#ef4444', // Green for buy, Red for short
          shape: isLong ? 'arrowUp' : 'arrowDown',
          text: isLong ? 'Buy' : 'Short',
          size: 1,
        });
      }

      // 2. Exit Marker
      if (trade.exit_time) {
        const exitTime = formatTime(trade.exit_time);
        if (exitTime) {
          markers.push({
            time: exitTime,
            position: isLong ? 'aboveBar' : 'belowBar',
            color: isLong ? '#f97316' : '#3b82f6', // Orange for exit long, Blue for cover short
            shape: isLong ? 'arrowDown' : 'arrowUp',
            text: isLong ? 'Exit' : 'Cover',
            size: 1,
          });
        }
      }
    });

    // Sort markers by time ascending (mandatory for lightweight-charts)
    markers.sort((a, b) => {
      if (typeof a.time === 'number' && typeof b.time === 'number') {
        return a.time - b.time;
      }
      return new Date(a.time).getTime() - new Date(b.time).getTime();
    });

    // Create Lightweight Chart instance
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: isDark ? '#111111' : '#ffffff' },
        textColor: isDark ? '#a1a1aa' : '#64748b',
        fontFamily: 'Inter, system-ui, sans-serif',
      },
      grid: {
        vertLines: { color: isDark ? '#27272a' : '#f1f5f9' },
        horzLines: { color: isDark ? '#27272a' : '#f1f5f9' },
      },
      crosshair: {
        mode: 1, // Magnet mode
      },
      rightPriceScale: {
        borderColor: isDark ? '#27272a' : '#e2e8f0',
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      timeScale: {
        borderColor: isDark ? '#27272a' : '#e2e8f0',
        timeVisible: true,
        secondsVisible: false,
      },
      width: chartContainerRef.current.clientWidth,
      height: 350,
    });

    // Add Candlestick Series
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    candlestickSeries.setData(uniqueData as any);

    // Apply markers to candlestick series if any exist
    if (markers.length > 0) {
      createSeriesMarkers(candlestickSeries, markers);
    }

    // Fit content inside the viewport
    chart.timeScale().fitContent();

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [ohlcData, trades, timeframe, resolvedTheme]);

  return (
    <div className="w-full relative">
      <div ref={chartContainerRef} className="w-full h-[350px]" />
    </div>
  );
}
