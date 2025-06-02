import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useNavigationStore } from '../../store/navigationStore';

interface Command {
  id: string;
  label: string;
  description: string;
  category: 'navigation' | 'agent' | 'system' | 'recent';
  action: () => void;
  icon: string;
  keywords?: string[];
}

interface CommandPaletteProps {
  className?: string;
}

export function CommandPalette({ className = '' }: CommandPaletteProps) {
  const navigate = useNavigate();
  const { isCommandPaletteOpen, toggleCommandPalette } = useNavigationStore();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Define all available commands
  const allCommands: Command[] = useMemo(() => [
    // Navigation commands
    {
      id: 'nav-dashboard',
      label: 'Dashboard',
      description: 'Go to system overview',
      category: 'navigation',
      icon: '◉',
      action: () => navigate('/'),
      keywords: ['home', 'main', 'overview']
    },
    {
      id: 'nav-inbox',
      label: 'Inbox',
      description: 'Check messages and notifications',
      category: 'navigation',
      icon: '📧',
      action: () => navigate('/inbox'),
      keywords: ['messages', 'notifications', 'mail']
    },
    {
      id: 'nav-knowledge',
      label: 'Knowledge Base',
      description: 'Browse documents and data',
      category: 'navigation',
      icon: '📚',
      action: () => navigate('/knowledge'),
      keywords: ['docs', 'documents', 'data', 'search']
    },
    {
      id: 'nav-agents',
      label: 'Agents',
      description: 'Manage AI agents',
      category: 'navigation',
      icon: '🤖',
      action: () => navigate('/agents'),
      keywords: ['ai', 'automation', 'bots']
    },
    {
      id: 'nav-terminal',
      label: 'Terminal',
      description: 'Command line interface',
      category: 'navigation',
      icon: '⌘',
      action: () => navigate('/terminal'),
      keywords: ['cli', 'command', 'shell']
    },
    {
      id: 'nav-logs',
      label: 'System Logs',
      description: 'View system activity',
      category: 'navigation',
      icon: '📝',
      action: () => navigate('/logs'),
      keywords: ['history', 'activity', 'debug']
    },
    {
      id: 'nav-settings',
      label: 'Settings',
      description: 'System configuration',
      category: 'navigation',
      icon: '⚙️',
      action: () => navigate('/settings'),
      keywords: ['config', 'preferences', 'options']
    },
    // Agent commands
    {
      id: 'agent-run',
      label: 'Run Agent',
      description: 'Execute an AI agent',
      category: 'agent',
      icon: '▶️',
      action: () => console.log('Run agent command'),
      keywords: ['execute', 'start', 'launch']
    },
    {
      id: 'agent-stop',
      label: 'Stop All Agents',
      description: 'Halt all running agents',
      category: 'agent',
      icon: '⏹️',
      action: () => console.log('Stop agents command'),
      keywords: ['halt', 'terminate', 'kill']
    },
    // System commands
    {
      id: 'system-restart',
      label: 'Restart System',
      description: 'Restart the AIOS system',
      category: 'system',
      icon: '⟲',
      action: () => console.log('Restart system command'),
      keywords: ['reboot', 'refresh', 'reload']
    },
    {
      id: 'system-status',
      label: 'System Status',
      description: 'Check system health',
      category: 'system',
      icon: '💚',
      action: () => console.log('System status command'),
      keywords: ['health', 'check', 'monitor']
    }
  ], [navigate]);

  // Fuzzy search implementation
  const filteredCommands = useMemo(() => {
    if (!query.trim()) {
      // Show recent/frequent commands when no query
      return allCommands.slice(0, 8);
    }

    const searchTerm = query.toLowerCase();
    
    return allCommands
      .map(command => ({
        ...command,
        score: calculateScore(command, searchTerm)
      }))
      .filter(command => command.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 10);
  }, [query, allCommands]);

  // Simple scoring algorithm for fuzzy search
  const calculateScore = (command: Command, searchTerm: string): number => {
    const label = command.label.toLowerCase();
    const description = command.description.toLowerCase();
    const keywords = command.keywords?.join(' ').toLowerCase() || '';
    
    let score = 0;
    
    // Exact match in label
    if (label.includes(searchTerm)) score += 100;
    
    // Partial match in label
    if (label.startsWith(searchTerm)) score += 50;
    
    // Match in description
    if (description.includes(searchTerm)) score += 30;
    
    // Match in keywords
    if (keywords.includes(searchTerm)) score += 40;
    
    // Character-by-character matching for fuzzy search
    let labelIndex = 0;
    let searchIndex = 0;
    while (labelIndex < label.length && searchIndex < searchTerm.length) {
      if (label[labelIndex] === searchTerm[searchIndex]) {
        score += 10;
        searchIndex++;
      }
      labelIndex++;
    }
    
    return searchIndex === searchTerm.length ? score : 0;
  };

  const executeCommand = useCallback((command: Command) => {
    command.action();
    toggleCommandPalette();
    setQuery('');
    setSelectedIndex(0);
  }, [toggleCommandPalette]);

  const handleClose = useCallback(() => {
    toggleCommandPalette();
    setQuery('');
    setSelectedIndex(0);
  }, [toggleCommandPalette]);

  // Keyboard navigation
  useEffect(() => {
    if (!isCommandPaletteOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev < filteredCommands.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev > 0 ? prev - 1 : filteredCommands.length - 1
          );
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            executeCommand(filteredCommands[selectedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          handleClose();
          break;
        case 'Tab':
          e.preventDefault();
          // Auto-complete with first result
          if (filteredCommands[0]) {
            setQuery(filteredCommands[0].label);
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isCommandPaletteOpen, filteredCommands, selectedIndex, executeCommand, handleClose]);

  // Focus input when opened
  useEffect(() => {
    if (isCommandPaletteOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isCommandPaletteOpen]);

  // Reset state when opening
  useEffect(() => {
    if (isCommandPaletteOpen) {
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isCommandPaletteOpen]);

  const highlightMatch = (text: string, query: string) => {
    if (!query.trim()) return text;
    
    const regex = new RegExp(`(${query})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => (
      regex.test(part) ? (
        <span key={index} className="bg-terminal-cyan text-black font-bold">
          {part}
        </span>
      ) : (
        <span key={index}>{part}</span>
      )
    ));
  };

  const getCategoryLabel = (category: string) => {
    const labels = {
      navigation: '🧭 Navigation',
      agent: '🤖 Agents',
      system: '⚙️ System',
      recent: '⏱️ Recent'
    };
    return labels[category as keyof typeof labels] || category;
  };

  if (!isCommandPaletteOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 px-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />
      
      {/* Command Palette */}
      <div className={`relative w-full max-w-2xl bg-nav-bg border border-nav-border rounded-lg shadow-2xl animate-slideDown ${className}`}>
        {/* Header */}
        <div className="flex items-center p-4 border-b border-nav-border">
          <span className="font-terminal text-terminal-cyan mr-3">⌘</span>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search..."
            className="flex-1 bg-transparent text-nav-text font-terminal text-lg outline-none placeholder-nav-text-dim"
          />
          <div className="text-nav-text-dim font-terminal text-xs">
            ESC to close
          </div>
        </div>

        {/* Results */}
        <div ref={listRef} className="max-h-96 overflow-y-auto">
          {filteredCommands.length > 0 ? (
            <div className="p-2">
              {/* Group by category */}
              {Object.entries(
                filteredCommands.reduce((acc, command) => {
                  if (!acc[command.category]) acc[command.category] = [];
                  acc[command.category].push(command);
                  return acc;
                }, {} as Record<string, typeof filteredCommands>)
              ).map(([category, commands], categoryIndex) => (
                <div key={category} className={categoryIndex > 0 ? 'mt-4' : ''}>
                  <div className="px-3 py-1 text-nav-text-dim font-terminal text-xs uppercase tracking-wider">
                    {getCategoryLabel(category)}
                  </div>
                  {commands.map((command, index) => {
                    const globalIndex = filteredCommands.indexOf(command);
                    const isSelected = globalIndex === selectedIndex;
                    
                    return (
                      <button
                        key={command.id}
                        onClick={() => executeCommand(command)}
                        className={`w-full text-left p-3 rounded-lg transition-all duration-200 ${
                          isSelected
                            ? 'bg-nav-active text-terminal-cyan scale-105'
                            : 'text-nav-text hover:bg-nav-hover hover:text-terminal-cyan'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <span className="text-lg">{command.icon}</span>
                          <div className="flex-1 min-w-0">
                            <div className="font-terminal text-sm">
                              {highlightMatch(command.label, query)}
                            </div>
                            <div className="text-xs text-nav-text-dim mt-1 truncate">
                              {command.description}
                            </div>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center">
              <div className="text-4xl mb-2">🔍</div>
              <div className="text-nav-text font-terminal">No commands found</div>
              <div className="text-nav-text-dim text-sm mt-1">
                Try a different search term
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-nav-border p-3">
          <div className="flex items-center justify-between text-xs text-nav-text-dim font-terminal">
            <div className="flex space-x-4">
              <span>↑↓ navigate</span>
              <span>⏎ select</span>
              <span>⇥ autocomplete</span>
            </div>
            <div>
              {filteredCommands.length} results
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 