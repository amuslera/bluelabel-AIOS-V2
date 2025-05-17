import React from 'react';

interface GreenButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'warning' | 'error';
  children: React.ReactNode;
}

export const GreenButton: React.FC<GreenButtonProps> = ({ 
  variant = 'primary', 
  children, 
  className = '',
  ...props 
}) => {
  const variants = {
    primary: 'bg-terminal-green/10 border-terminal-green text-terminal-green hover:bg-terminal-green/20',
    secondary: 'bg-terminal-green-dark/10 border-terminal-green-dark text-terminal-green-dark hover:bg-terminal-green-dark/20',
    warning: 'bg-terminal-amber/10 border-terminal-amber text-terminal-amber hover:bg-terminal-amber/20',
    error: 'bg-error-pink/10 border-error-pink text-error-pink hover:bg-error-pink/20'
  };

  return (
    <button
      className={`px-4 py-2 font-mono uppercase transition-all duration-200 border ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};