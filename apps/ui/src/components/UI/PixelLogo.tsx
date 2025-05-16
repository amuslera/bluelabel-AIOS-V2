import React from 'react';

export const PixelLogo: React.FC = () => {
  return (
    <div className="text-center">
      <div className="inline-block">
        <div className="text-6xl font-bold mb-4" style={{ 
          fontFamily: 'VT323, monospace',
          letterSpacing: '0.1em',
          textShadow: '2px 2px 0px rgba(0, 0, 0, 0.5)'
        }}>
          <span className="text-cyan-400">BLUELABEL</span>
        </div>
        <div className="text-5xl font-bold" style={{ 
          fontFamily: 'VT323, monospace',
          letterSpacing: '0.1em',
          textShadow: '2px 2px 0px rgba(0, 0, 0, 0.5)'
        }}>
          <span className="text-cyan-400">AIOS</span>
        </div>
      </div>
    </div>
  );
};