import React from 'react';

interface InfoBoxProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const InfoBox: React.FC<InfoBoxProps> = ({ title, children, className = '' }) => {
  const borderChar = '─';
  const cornerTL = '┌';
  const cornerTR = '┐';
  const cornerBL = '└';
  const cornerBR = '┘';
  const verticalChar = '│';
  
  return (
    <div className={`relative ${className}`}>
      {/* Top border */}
      <div className="text-terminal-green font-mono text-sm leading-none">
        <span>{cornerTL}</span>
        <span>{borderChar.repeat(50)}</span>
        {title && (
          <>
            <span>{' '}</span>
            <span className="text-terminal-green font-bold">{title}</span>
            <span>{' '}</span>
          </>
        )}
        <span>{borderChar.repeat(title ? 50 - title.length - 2 : 50)}</span>
        <span>{cornerTR}</span>
      </div>
      
      {/* Content */}
      <div className="px-6 py-4">
        {children}
      </div>
      
      {/* Bottom border */}
      <div className="text-terminal-green font-mono text-sm leading-none">
        <span>{cornerBL}</span>
        <span>{borderChar.repeat(100)}</span>
        <span>{cornerBR}</span>
      </div>
    </div>
  );
};