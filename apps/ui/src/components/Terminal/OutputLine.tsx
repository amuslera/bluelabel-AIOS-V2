import React from 'react';

export interface OutputLineData {
  type: 'command' | 'output' | 'error' | 'info' | 'system';
  content: string;
  timestamp?: string;
}

interface OutputLineProps extends OutputLineData {
  showTimestamp?: boolean;
}

export const OutputLine: React.FC<OutputLineProps> = ({
  type,
  content,
  timestamp,
  showTimestamp = false,
}) => {
  const getColorClass = () => {
    switch (type) {
      case 'command':
        return 'text-terminal-cyan retro-glow';
      case 'error':
        return 'text-error-pink';
      case 'info':
        return 'text-terminal-amber';
      case 'system':
        return 'text-terminal-cyan/80';
      default:
        return 'text-terminal-cyan';
    }
  };

  const formatContent = () => {
    if (type === 'command') {
      return `> ${content}`;
    }
    return content;
  };

  return (
    <div className={`font-terminal ${getColorClass()} whitespace-pre-wrap`}>
      {showTimestamp && timestamp && (
        <span className="text-terminal-cyan/50">[{timestamp}] </span>
      )}
      {formatContent()}
    </div>
  );
};