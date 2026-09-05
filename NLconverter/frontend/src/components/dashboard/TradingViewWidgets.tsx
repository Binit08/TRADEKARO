"use client";
import React, { useEffect, useRef } from 'react';
import { useTheme } from 'next-themes';
import { Panel } from '@/components/ui/Panel';

export const IndexTape = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    
    // Clear existing to prevent duplicates
    container.innerHTML = '';

    const widget = document.createElement('div');
    widget.className = 'tradingview-widget-container';
    widget.style.height = '100%';
    widget.style.width = '100%';

    const widgetContent = document.createElement('div');
    widgetContent.className = 'tradingview-widget-container__widget';
    widget.appendChild(widgetContent);

    const widgetScript = document.createElement('script');
    widgetScript.type = 'text/javascript';
    widgetScript.src = 'https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js';
    widgetScript.async = true;
    widgetScript.textContent = JSON.stringify({
      symbols: [
        { proName: 'BSE:SENSEX', title: 'SENSEX' },
        { proName: 'BSE:RELIANCE', title: 'RELIANCE' },
        { proName: 'BSE:TCS', title: 'TCS' },
        { proName: 'BSE:HDFCBANK', title: 'HDFCBANK' },
        { proName: 'BSE:INFY', title: 'INFY' },
        { proName: 'BSE:ICICIBANK', title: 'ICICIBANK' },
        { proName: 'BSE:SBIN', title: 'SBIN' },
        { proName: 'BSE:BHARTIARTL', title: 'BHARTIARTL' },
        { proName: 'BSE:ITC', title: 'ITC' },
        { proName: 'BSE:LT', title: 'LT' }
      ],
      showSymbolLogo: true,
      colorTheme: resolvedTheme === 'dark' ? 'dark' : 'light',
      isTransparent: false,
      displayMode: 'adaptive',
      locale: 'en'
    });
    widget.appendChild(widgetScript);

    container.appendChild(widget);

    return () => {
      container.innerHTML = '';
    };
  }, [resolvedTheme]);

  return (
    <div
      ref={containerRef}
      className="w-full overflow-hidden bg-surface border-b border-border py-0.5"
      style={{ minHeight: '46px' }}
    />
  );
};

export const Watchlist = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    
    container.innerHTML = '';

    const widget = document.createElement('div');
    widget.className = 'tradingview-widget-container';
    widget.style.height = '100%';
    widget.style.width = '100%';

    const widgetContent = document.createElement('div');
    widgetContent.className = 'tradingview-widget-container__widget';
    widgetContent.style.height = 'calc(100% - 32px)';
    widgetContent.style.width = '100%';
    widget.appendChild(widgetContent);

    const copyright = document.createElement('div');
    copyright.className = 'tradingview-widget-copyright';
    copyright.innerHTML =
      '<a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank"><span class="blue-text">Track all markets on TradingView</span></a>';
    widget.appendChild(copyright);

    const widgetScript = document.createElement('script');
    widgetScript.type = 'text/javascript';
    widgetScript.src = 'https://s3.tradingview.com/external-embedding/embed-widget-market-quotes.js';
    widgetScript.async = true;
    widgetScript.textContent = JSON.stringify({
      width: '100%',
      height: 750,
      symbolsGroups: [
        {
          name: 'Indian Stocks',
          originalName: 'Indian Stocks',
          symbols: [
            { name: 'BSE:RELIANCE', displayName: 'RELIANCE' },
            { name: 'BSE:SBIN', displayName: 'SBIN' },
            { name: 'BSE:INFY', displayName: 'INFY' },
            { name: 'BSE:TCS', displayName: 'TCS' },
            { name: 'BSE:HDFCBANK', displayName: 'HDFCBANK' },
            { name: 'BSE:LT', displayName: 'LT' },
            { name: 'BSE:ITC', displayName: 'ITC' }
          ]
        },
        {
          name: 'Indices',
          originalName: 'Indices',
          symbols: [
            { name: 'BSE:SENSEX', displayName: 'SENSEX' },
            { name: 'FOREXCOM:SPXUSD', displayName: 'S&P 500' },
            { name: 'FOREXCOM:NSXUSD', displayName: 'US 100' }
          ]
        },
        {
          name: 'Forex & Crypto',
          originalName: 'Forex & Crypto',
          symbols: [
            { name: 'FX:EURUSD', displayName: 'EUR to USD' },
            { name: 'BITSTAMP:BTCUSD', displayName: 'Bitcoin' },
            { name: 'BITSTAMP:ETHUSD', displayName: 'Ethereum' }
          ]
        }
      ],
      showSymbolLogo: true,
      isTransparent: false,
      colorTheme: resolvedTheme === 'dark' ? 'dark' : 'light',
      locale: 'en'
    });
    widget.appendChild(widgetScript);

    container.appendChild(widget);

    return () => {
      container.innerHTML = '';
    };
  }, [resolvedTheme]);

  return (
    <Panel title="Watchlist" className="flex-1 min-h-[750px]">
      <div ref={containerRef} className="h-full w-full overflow-hidden" />
    </Panel>
  );
};

export const Screener = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    
    container.innerHTML = '';

    const widget = document.createElement('div');
    widget.className = 'tradingview-widget-container';
    widget.style.height = '100%';
    widget.style.width = '100%';

    const widgetContent = document.createElement('div');
    widgetContent.className = 'tradingview-widget-container__widget';
    widgetContent.style.height = 'calc(100% - 32px)';
    widgetContent.style.width = '100%';
    widget.appendChild(widgetContent);

    const copyright = document.createElement('div');
    copyright.className = 'tradingview-widget-copyright';
    copyright.innerHTML =
      '<a href="https://www.tradingview.com/screener/" rel="noopener nofollow" target="_blank"><span class="blue-text">Stock Screener</span></a><span class="trademark"> by TradingView</span>';
    widget.appendChild(copyright);

    const widgetScript = document.createElement('script');
    widgetScript.type = 'text/javascript';
    widgetScript.src = 'https://s3.tradingview.com/external-embedding/embed-widget-screener.js';
    widgetScript.async = true;
    widgetScript.textContent = JSON.stringify({
      market: 'india',
      showToolbar: true,
      defaultColumn: 'overview',
      defaultScreen: 'most_capitalized',
      isTransparent: false,
      locale: 'en',
      colorTheme: resolvedTheme === 'dark' ? 'dark' : 'light',
      width: '100%',
      height: Math.max(window.innerHeight - 220, 500),
    });
    widget.appendChild(widgetScript);

    container.appendChild(widget);

    return () => {
      container.innerHTML = '';
    };
  }, [resolvedTheme]);

  return (
    <Panel title="Stock Screener" className="w-full h-[calc(100vh-160px)]">
      <div ref={containerRef} className="w-full h-full" />
    </Panel>
  );
};
