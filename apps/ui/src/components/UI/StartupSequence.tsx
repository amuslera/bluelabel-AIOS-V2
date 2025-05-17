import React, { useState, useEffect } from 'react';
import { ProgressBar } from './ProgressBar';

interface StartupSequenceProps {
  onComplete: () => void;
}

export const StartupSequence: React.FC<StartupSequenceProps> = ({ onComplete }) => {
  const [currentLine, setCurrentLine] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  const startupMessages = [
    'COMMODORE 64 BASIC V2',
    '64K RAM SYSTEM  38911 BASIC BYTES FREE',
    'READY.',
    'LOAD "BLUELABEL",8,1',
    'SEARCHING FOR BLUELABEL',
    'LOADING',
    'READY.',
    'RUN',
    'INITIALIZING BLUELABEL AIOS V2.0...',
    'LOADING SYSTEM MODULES...',
    'CONNECTING TO NETWORK...',
    'SYSTEM READY'
  ];

  useEffect(() => {
    if (currentLine < startupMessages.length) {
      const timer = setTimeout(() => {
        setCurrentLine(currentLine + 1);
      }, 400); // Doubled the time between messages
      return () => clearTimeout(timer);
    } else if (!isComplete) {
      setIsComplete(true);
      setTimeout(onComplete, 2000); // Show completion for 2 seconds
    }
  }, [currentLine, startupMessages.length, isComplete, onComplete]);

  return (
    <div className="fixed inset-0 bg-black z-50 flex flex-col">
      <div className="flex-1 flex items-center justify-center">
        <div className="text-cyan-400 font-mono">
          {startupMessages.slice(0, currentLine).map((message, index) => (
            <div key={index} className="mb-1">
              {message}
            </div>
          ))}
          {currentLine < startupMessages.length && (
            <div className="inline-block animate-pulse">█</div>
          )}
        </div>
      </div>
      
      {/* Progress bar at the bottom */}
      <div className="p-8">
        <ProgressBar 
          progress={(currentLine / startupMessages.length) * 100}
          text="LOADING BLUELABEL AIOS"
          showPercentage={true}
        />
      </div>
    </div>
  );
};