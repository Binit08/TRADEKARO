import React from 'react';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
}

export const EmptyState = ({ icon: Icon, title, description, actionText, onAction }: EmptyStateProps) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center h-full">
      <div className="w-16 h-16 bg-muted/10 rounded-full flex items-center justify-center mb-6">
        <Icon size={32} className="text-muted" />
      </div>
      <h3 className="text-lg font-bold text-foreground mb-2" style={{ fontFamily: '"Space Grotesk", sans-serif' }}>
        {title}
      </h3>
      <p className="text-sm text-muted max-w-sm mb-8">
        {description}
      </p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-6 py-2.5 bg-accent-primary text-white rounded-lg text-sm font-medium hover:opacity-90 active:scale-95 transition-all shadow-sm"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
