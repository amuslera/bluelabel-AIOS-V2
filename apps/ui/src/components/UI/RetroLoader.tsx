import React from 'react';

interface RetroLoaderProps {
  text?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const RetroLoader: React.FC<RetroLoaderProps> = ({ 
  text = 'Loading...', 
  size = 'md' 
}) => {
  const sizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-xl',
  };

  return (
    <div className={`flex flex-col items-center justify-center space-y-4 ${sizeClasses[size]}`}>
      <div className="flex space-x-1">
        {[...Array(8)].map((_, i) => (
          <div
            key={i}
            className="w-2 h-8 bg-cyan animate-pulse"
            style={{
              animationDelay: `${i * 0.1}s`,
              height: `${Math.sin((i / 7) * Math.PI) * 32 + 16}px`,
            }}
          />
        ))}
      </div>
      <p className="text-cyan animate-pulse">{text}</p>
    </div>
  );
};