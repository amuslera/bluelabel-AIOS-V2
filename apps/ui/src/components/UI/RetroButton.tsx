import React from 'react';

interface RetroButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'success' | 'error' | 'warning';
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}

export const RetroButton: React.FC<RetroButtonProps> = ({
  children,
  variant = 'primary',
  onClick,
  disabled = false,
  className = '',
}) => {
  const variants = {
    primary: 'border-terminal-cyan text-terminal-cyan hover:bg-terminal-cyan/10',
    success: 'border-terminal-green text-terminal-green hover:bg-terminal-green/10',
    error: 'border-error-pink text-error-pink hover:bg-error-pink/10',
    warning: 'border-terminal-amber text-terminal-amber hover:bg-terminal-amber/10',
  };

  return (
    <button
      className={`
        px-4 py-2 border-2 font-terminal uppercase
        transition-all duration-200
        ${variants[variant]}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        shadow-[2px_2px_0px_0px_rgba(0,255,255,0.3)]
        hover:shadow-[4px_4px_0px_0px_rgba(0,255,255,0.5)]
        hover:retro-glow
        active:transform active:translate-y-0.5
        ${className}
      `}
      onClick={onClick}
      disabled={disabled}
    >
      [{children}]
    </button>
  );
};
