import React from 'react';

export const PixelLogo: React.FC = () => {
  // Create multiple layers for the 3D effect similar to Boulder Dash
  const createShadow = () => {
    const shadows = [];
    const colors = [
      '#ff6600', // Orange
      '#ff9900', // Light orange
      '#ffcc00', // Yellow
      '#33ff00', // Green
      '#00ffcc', // Cyan
      '#0099ff', // Blue
      '#6633ff', // Purple
      '#cc00ff', // Magenta
    ];
    
    // Create sharp outline
    shadows.push('-2px -2px 0 #000');
    shadows.push('2px -2px 0 #000');
    shadows.push('-2px 2px 0 #000');
    shadows.push('2px 2px 0 #000');
    
    // Create 3D layers
    colors.forEach((color, index) => {
      const offset = (index + 1) * 2;
      shadows.push(`${offset}px ${offset}px 0 ${color}`);
    });
    
    return shadows.join(', ');
  };

  return (
    <div className="text-center relative">
      <div className="inline-block">
        <div 
          className="text-5xl font-bold"
          style={{ 
            fontFamily: '"Press Start 2P", monospace',
            color: '#ffffff',
            textShadow: createShadow(),
            textTransform: 'uppercase',
            letterSpacing: '-0.02em',
            padding: '30px',
            WebkitFontSmoothing: 'none',
            imageRendering: 'pixelated'
          }}
        >
          BLUELABEL AIOS
        </div>
      </div>
    </div>
  );
};