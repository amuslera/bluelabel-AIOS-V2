import React, { useState, useRef, useEffect } from 'react';
import { CommandInput } from './CommandInput';
import { OutputLine, OutputLineData } from './OutputLine';
import { terminalCommands } from '../../utils/terminalCommands';

export const Terminal: React.FC = () => {
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<OutputLineData[]>([
    {
      type: 'system',
      content: 'BLUELABEL AIOS TERMINAL v2.0',
    },
    {
      type: 'system',
      content: 'Type "help" for available commands',
    },
  ]);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const outputRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to bottom when new output is added
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [history]);

  const executeCommand = async (cmd: string) => {
    const trimmedCmd = cmd.trim();
    if (!trimmedCmd) return;

    // Add command to history
    const newHistory = [...history, { type: 'command' as const, content: trimmedCmd }];
    setHistory(newHistory);
    setCommandHistory([...commandHistory, trimmedCmd]);
    setHistoryIndex(-1);

    // Parse command
    const [command, ...args] = trimmedCmd.split(' ');
    
    try {
      // Execute command
      const result = await terminalCommands.execute(command, args);
      
      if (result.output) {
        setHistory([...newHistory, {
          type: result.type || 'output',
          content: result.output,
        }]);
      }
      
      if (result.clear) {
        setHistory([]);
      }
    } catch (error) {
      setHistory([...newHistory, {
        type: 'error',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      }]);
    }
  };

  const handleSubmit = (value: string) => {
    executeCommand(value);
    setInput('');
  };

  const handleHistoryNavigate = (direction: 'up' | 'down') => {
    if (commandHistory.length === 0) return;

    let newIndex = historyIndex;
    if (direction === 'up') {
      newIndex = historyIndex === -1 
        ? commandHistory.length - 1 
        : Math.max(0, historyIndex - 1);
    } else {
      newIndex = historyIndex === -1 
        ? -1 
        : Math.min(commandHistory.length - 1, historyIndex + 1);
    }

    setHistoryIndex(newIndex);
    setInput(newIndex === -1 ? '' : commandHistory[newIndex]);
  };

  return (
    <div className="border-2 border-terminal-cyan p-4 ascii-border bg-terminal-dark h-full flex flex-col">
      <div className="text-terminal-cyan mb-4 text-lg font-bold retro-glow">
        TERMINAL
      </div>
      
      <div 
        ref={outputRef}
        className="flex-1 overflow-y-auto mb-4 space-y-1"
      >
        {history.map((line, index) => (
          <OutputLine key={index} {...line} />
        ))}
      </div>
      
      <CommandInput
        value={input}
        onChange={setInput}
        onSubmit={handleSubmit}
        onHistoryNavigate={handleHistoryNavigate}
      />
    </div>
  );
};