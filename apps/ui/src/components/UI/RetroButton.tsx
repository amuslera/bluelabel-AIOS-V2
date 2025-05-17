import React from 'react';

interface RetroButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'warning' | 'error' | 'success';
  children: React.ReactNode;
}

export const RetroButton: React.FC<RetroButtonProps> = ({ 
  variant = 'primary', 
  children, 
  className = '',
  ...props 
}) => {
  const variants = {
    primary: 'bg-cyan-500 hover:bg-cyan-400 text-black',
    secondary: 'bg-green-500 hover:bg-green-400 text-black',
    warning: 'bg-yellow-500 hover:bg-yellow-400 text-black',
    error: 'bg-red-500 hover:bg-red-400 text-white',
    success: 'bg-green-500 hover:bg-green-400 text-black'
  };

  return (
    <button
      className={`px-4 py-2 font-bold uppercase transition-colors ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};