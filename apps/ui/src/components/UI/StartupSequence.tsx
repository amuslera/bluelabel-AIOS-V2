import React, { useState, useEffect } from 'react';

interface StartupSequenceProps {
  onComplete: () => void;
}

export const StartupSequence: React.FC<StartupSequenceProps> = ({ onComplete }) => {
  const [messages, setMessages] = useState<string[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  const startupMessages = [
    '>> Initializing Bluelabel AIOS...',
    '>> Authenticating session...',
    '>> Loading ContentMind agent...',
    '>> Connecting to Redis stream...',
    '>> AIOS v2 booted. Awaiting input.'
  ];

  useEffect(() => {
    if (currentIndex < startupMessages.length) {
      const timer = setTimeout(() => {
        setMessages(prev => [...prev, startupMessages[currentIndex]]);
        setCurrentIndex(prev => prev + 1);
      }, 300);
      return () => clearTimeout(timer);
    } else {
      setTimeout(onComplete, 500);
    }
  }, [currentIndex, startupMessages, onComplete]);

  return (
    <div className="min-h-screen bg-slate-900 text-cyan-400 p-8 font-terminal">
      <div className="max-w-4xl mx-auto">
        {messages.map((message, index) => (
          <div key={index} className="mb-2 text-lg">
            {message}
          </div>
        ))}
        {currentIndex >= startupMessages.length && (
          <div className="mt-8 border-2 border-cyan-400 p-2 inline-block">
            <span className="text-cyan-400">&gt;_</span>
          </div>
        )}
      </div>
    </div>
  );
};