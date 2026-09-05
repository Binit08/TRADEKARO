"use client";

import { useEffect, useRef } from "react";
import { createChart, CandlestickData, Time, SeriesMarker, CandlestickSeries, createSeriesMarkers } from "lightweight-charts";
import { useTheme } from "next-themes";

interface PaperTradeChartProps {
  sessionId: string;
}

export default function PaperTradeChart({ sessionId }: PaperTradeChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const { resolvedTheme } = useTheme();
  
  // We maintain a reference to markers so we can append them from both history and live ws updates
  const markersRef = useRef<SeriesMarker<Time>[]>([]);

  useEffect(() => {
    if (!chartContainerRef.current) return;
    
    const isDark = resolvedTheme === 'dark';

    // 1. Initialize Chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: isDark ? '#111111' : '#ffffff' },
        textColor: isDark ? '#A1A1AA' : '#333',
      },
      grid: {
        vertLines: { color: isDark ? '#27272A' : '#f0f0f0' },
        horzLines: { color: isDark ? '#27272A' : '#f0f0f0' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#e0e0e0',
      },
      timeScale: {
        borderColor: '#e0e0e0',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    const seriesMarkers = createSeriesMarkers(candlestickSeries, []);

    // We connect directly to the Backtesting Engine on port 8002 for paper trading endpoints
    const API_URL = process.env.NEXT_PUBLIC_BACKTEST_API_URL || 'http://127.0.0.1:8002';
    const WS_URL = API_URL.replace('http', 'ws');

    // Helper to fix Lightweight Charts timezone bug (it plots Unix timestamps as UTC)
    const tzOffsetSeconds = new Date().getTimezoneOffset() * 60;
    const parseLocalTime = (timestamp: string | number) => {
      let utcSeconds;
      if (typeof timestamp === "string") {
        // Fix Python's str(datetime) which outputs "YYYY-MM-DD HH:MM:SS.mmmmmm+HH:MM"
        // Many browsers (like Safari) require "T" instead of a space.
        const safeStr = timestamp.replace(" ", "T");
        utcSeconds = Math.floor(new Date(safeStr).getTime() / 1000);
        if (isNaN(utcSeconds)) {
          console.error("Invalid date parsed:", timestamp);
        }
      } else {
        utcSeconds = timestamp as number;
      }
      return (utcSeconds - tzOffsetSeconds) as Time;
    };

        // 2. Fetch History
        let primarySymbol: string | null = null;
        
    fetch(`/api/proxy/paper_trade/${sessionId}/history`)
      .then((res) => res.json())
      .then((data) => {
        if (!data.history) return;
        
        const historicalCandles: CandlestickData[] = [];
        const newMarkers: SeriesMarker<Time>[] = [];

        // Parse candles
        if (data.history.candles) {
          data.history.candles.forEach((candle: any) => {
            if (!primarySymbol && candle.symbol) primarySymbol = candle.symbol;
            if (primarySymbol && candle.symbol && candle.symbol !== primarySymbol) return;
            
            const time = parseLocalTime(candle.timestamp || candle.time);
            historicalCandles.push({
              time,
              open: candle.open,
              high: candle.high,
              low: candle.low,
              close: candle.close,
            });
          });
        }

        // Parse fills (trades)
        if (data.history.fills) {
          data.history.fills.forEach((fill: any) => {
            if (primarySymbol && fill.symbol && fill.symbol !== primarySymbol) return;
            const time = parseLocalTime(fill.timestamp || fill.time);
            newMarkers.push({
              time,
              position: fill.side === 'BUY' ? 'belowBar' : 'aboveBar',
              color: fill.side === 'BUY' ? '#26a69a' : '#ef5350',
              shape: fill.side === 'BUY' ? 'arrowUp' : 'arrowDown',
              text: `${fill.side} @ ${fill.price}`,
            });
          });
        }
        
        candlestickSeries.setData(historicalCandles);
        markersRef.current = newMarkers;
        seriesMarkers.setMarkers(markersRef.current);
      })
      .catch((err) => console.error("Failed to fetch chart history:", err));

    // 3. Connect WebSocket for live updates
    const ws = new WebSocket(`${WS_URL}/api/v1/ws/paper_trade/${sessionId}`);
    
    ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      
      if (payload.type === "CANDLE_UPDATE") {
        const candleData = payload.data || payload;
        if (!primarySymbol && candleData.symbol) primarySymbol = candleData.symbol;
        if (primarySymbol && candleData.symbol && candleData.symbol !== primarySymbol) return;
        
        const time = parseLocalTime(candleData.timestamp || candleData.time);
        
        // Update candlestick
        try {
          candlestickSeries.update({
            time,
            open: candleData.open,
            high: candleData.high,
            low: candleData.low,
            close: candleData.close,
          });
        } catch (e) {
          console.error("CRASH PAYLOAD:", payload);
          console.error("PARSED TIME:", time);
          throw e; // rethrow to keep original error trace
        }

      } else if (payload.type === "FILL_UPDATE") {
        const fillData = payload.data || payload;
        if (primarySymbol && fillData.symbol && fillData.symbol !== primarySymbol) return;
        
        const time = parseLocalTime(fillData.timestamp || fillData.time);

        // Add marker
        markersRef.current.push({
          time,
          position: fillData.side === 'BUY' ? 'belowBar' : 'aboveBar',
          color: fillData.side === 'BUY' ? '#26a69a' : '#ef5350',
          shape: fillData.side === 'BUY' ? 'arrowUp' : 'arrowDown',
          text: `${fillData.side} @ ${fillData.price}`,
        });
        
        // Overwrite markers array to trigger update
        seriesMarkers.setMarkers(markersRef.current);
      }
    };

    ws.onerror = (err) => {
      // Native WebSocket error events don't contain details (they stringify to {})
      console.warn("Paper trade websocket connection issue. It may have been closed or dropped.");
    };

    ws.onclose = (event) => {
      if (event.code === 1008) {
        console.warn("WebSocket closed by server (1008): Session not found. It may have expired or the backend restarted.");
      } else if (event.code !== 1000) {
        console.warn(`WebSocket closed abnormally with code: ${event.code}`);
      }
    };

    const handleResize = () => {
      chart.applyOptions({ width: chartContainerRef.current?.clientWidth ?? 800 });
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      // Nullify handlers before closing to prevent errors from firing during unmount
      ws.onmessage = null;
      ws.onerror = null;
      ws.onclose = null;
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          ws.close();
      }
      chart.remove();
    };
  }, [sessionId, resolvedTheme]);

  return (
    <div className="w-full bg-surface rounded-xl shadow-sm border border-border p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-foreground">Live Paper Trading Chart</h3>
        <span className="flex items-center text-sm font-medium text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
          <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
          Live Stream Connected
        </span>
      </div>
      <div ref={chartContainerRef} className="w-full h-[400px]" />
    </div>
  );
}
