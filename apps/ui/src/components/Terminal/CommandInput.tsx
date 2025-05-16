import React, { useRef, useEffect } from 'react';

interface CommandInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
  onHistoryNavigate: (direction: 'up' | 'down') => void;
  prompt?: string;
}

export const CommandInput: React.FC<CommandInputProps> = ({
  value,
  onChange,
  onSubmit,
  onHistoryNavigate,
  prompt = '>',
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onSubmit(value);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      onHistoryNavigate('up');
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      onHistoryNavigate('down');
    }
  };

  return (
    <div className="flex items-center">
      <span className="text-terminal-cyan mr-2 retro-glow">{prompt}</span>
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        className="flex-1 bg-transparent border-none outline-none text-terminal-cyan font-terminal"
        autoFocus
      />
      <span className="text-terminal-cyan animate-blink retro-glow">_</span>
    </div>
  );
};