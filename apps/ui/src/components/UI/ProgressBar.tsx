import React from 'react';

interface ProgressBarProps {
  progress: number; // 0-100
  text?: string;
  showPercentage?: boolean;
  height?: string;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ 
  progress, 
  text, 
  showPercentage = true, 
  height = 'h-8',
  className = ''
}) => {
  return (
    <div className={`w-full ${height} bg-gray-800 relative overflow-hidden ${className}`}>
      <div 
        className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300 ease-out"
        style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
      />
      <div className="absolute inset-0 flex items-center justify-center text-white font-mono text-sm">
        {text || 'LOADING...'} {showPercentage && `${Math.round(progress)}%`}
      </div>
    </div>
  );
};