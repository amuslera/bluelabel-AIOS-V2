import React from 'react';
import { cn } from '../../utils/cn';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

export const Button: React.FC<ButtonProps> = ({ 
  className, 
  variant = 'default', 
  size = 'md',
  children,
  ...props 
}) => {
  const baseStyles = 'font-bold uppercase transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    default: 'bg-gray-800 text-green-400 hover:bg-gray-700 border border-cyan-500',
    primary: 'bg-cyan-500 text-black hover:bg-cyan-400',
    secondary: 'bg-purple-600 text-white hover:bg-purple-500',
    danger: 'bg-red-600 text-white hover:bg-red-500'
  };
  
  const sizes = {
    sm: 'px-3 py-1 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg'
  };
  
  return (
    <button
      className={cn(
        baseStyles,
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
};