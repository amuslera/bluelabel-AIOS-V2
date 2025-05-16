import React from 'react';

interface RetroCardProps {
  title?: string;
  children: React.ReactNode;
  variant?: 'default' | 'error' | 'success' | 'warning';
  className?: string;
}

export const RetroCard: React.FC<RetroCardProps> = ({
  title,
  children,
  variant = 'default',
  className = '',
}) => {
  const borderColors = {
    default: 'border-terminal-cyan',
    error: 'border-error-pink',
    success: 'border-terminal-green',
    warning: 'border-terminal-amber',
  };

  const titleColors = {
    default: 'text-terminal-cyan',
    error: 'text-error-pink',
    success: 'text-terminal-green',
    warning: 'text-terminal-amber',
  };

  return (
    <div className={`border-2 ${borderColors[variant]} p-4 bg-terminal-dark ascii-border ${className}`}>
      {title && (
        <h3 className={`text-xl mb-4 ${titleColors[variant]} font-bold retro-glow`}>
          {title}
        </h3>
      )}
      {children}
    </div>
  );
};