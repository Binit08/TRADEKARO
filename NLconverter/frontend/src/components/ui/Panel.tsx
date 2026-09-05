import React from 'react';

export const Panel = ({
  title,
  headerRight,
  children,
  className = ""
}: {
  title?: string;
  headerRight?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) => {
  return (
    <div
      className={`relative bg-surface flex flex-col rounded-xl shadow-sm hover:shadow-md transition-shadow duration-200 border border-border ${className}`}
    >

      {title && (
        <div
          className="px-5 py-3 flex items-center justify-between border-b border-border"
        >
          <h2
            className="font-bold tracking-widest uppercase text-foreground"
            style={{
              fontFamily: '"Space Grotesk", sans-serif',
              fontSize: '11px',
              letterSpacing: '0.08em'
            }}
          >
            {title}
          </h2>
          {headerRight && <div>{headerRight}</div>}
        </div>
      )}
      <div className="flex-1 overflow-auto p-5">
        {children}
      </div>
    </div>
  );
};
