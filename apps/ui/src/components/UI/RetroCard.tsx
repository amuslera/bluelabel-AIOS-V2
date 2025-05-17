import React from 'react';

interface RetroCardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const RetroCard: React.FC<RetroCardProps> = ({ title, children, className = '' }) => {
  return (
    <div className={`border-2 border-cyan-400 p-4 bg-black ${className}`}>
      {title && (
        <h3 className="text-cyan-400 text-lg font-bold mb-4 uppercase">{title}</h3>
      )}
      <div className="text-green-400">
        {children}
      </div>
    </div>
  );
};