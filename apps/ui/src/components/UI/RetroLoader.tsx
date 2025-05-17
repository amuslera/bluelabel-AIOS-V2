import React from 'react';

interface RetroLoaderProps {
  text?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const RetroLoader: React.FC<RetroLoaderProps> = ({ text, size = 'md' }) => {
  const sizes = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };

  return (
    <div className="flex flex-col items-center justify-center space-y-2">
      <div className={`animate-pulse text-cyan-400 ${sizes[size]}`}>
        [▓▓▓▓▓▓▓▓░░] LOADING...
      </div>
      {text && (
        <div className={`text-green-400 ${sizes[size]}`}>{text}</div>
      )}
    </div>
  );
};