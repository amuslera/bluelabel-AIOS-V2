import React from 'react';

export const RainbowStripe: React.FC = () => {
  return (
    <div className="flex h-2">
      <div className="flex-1 bg-red-500"></div>
      <div className="flex-1 bg-orange-500"></div>
      <div className="flex-1 bg-yellow-400"></div>
      <div className="flex-1 bg-green-500"></div>
      <div className="flex-1 bg-blue-500"></div>
      <div className="flex-1 bg-indigo-600"></div>
      <div className="flex-1 bg-purple-600"></div>
    </div>
  );
};