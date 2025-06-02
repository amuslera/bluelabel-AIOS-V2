import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useNavigationStore } from '../../store/navigationStore';

export function Breadcrumbs() {
  const navigate = useNavigate();
  const { breadcrumbs } = useNavigationStore();
  const [copied, setCopied] = useState(false);

  const copyPathToClipboard = async () => {
    const path = breadcrumbs.map(crumb => crumb.label.toLowerCase()).join(' > ');
    const terminalPath = `~/${path}`;
    
    try {
      await navigator.clipboard.writeText(terminalPath);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = terminalPath;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleBreadcrumbClick = (path: string) => {
    navigate(path);
  };

  if (breadcrumbs.length === 0) {
    return null;
  }

  // Truncate breadcrumbs on mobile
  const isMobile = window.innerWidth < 640;
  const displayBreadcrumbs = isMobile && breadcrumbs.length > 3 
    ? [
        breadcrumbs[0], 
        { label: '...', path: '', isActive: false }, 
        ...breadcrumbs.slice(-2)
      ]
    : breadcrumbs;

  return (
    <div className="flex items-center space-x-2 min-w-0">
      {/* Terminal prompt indicator */}
      <div className="flex items-center space-x-1 text-terminal-cyan">
        <span className="font-terminal text-sm">~/</span>
      </div>

      {/* Breadcrumb path */}
      <div className="flex items-center space-x-1 min-w-0 flex-1">
        {displayBreadcrumbs.map((crumb, index) => (
          <React.Fragment key={`${crumb.path}-${index}`}>
            {index > 0 && (
              <span className="text-nav-text-dim font-terminal text-sm select-none">
                {'>'}
              </span>
            )}
            
            {crumb.label === '...' ? (
              <span className="text-nav-text-dim font-terminal text-sm select-none">
                ...
              </span>
            ) : (
              <button
                onClick={() => handleBreadcrumbClick(crumb.path)}
                disabled={crumb.isActive}
                className={`
                  font-terminal text-sm transition-all duration-200 truncate
                  ${crumb.isActive 
                    ? 'text-terminal-cyan cursor-default' 
                    : 'text-nav-text hover:text-terminal-cyan hover:underline cursor-pointer'
                  }
                  ${crumb.isActive ? 'animate-pulse' : ''}
                `}
                title={`Navigate to ${crumb.label}`}
              >
                {crumb.label.toLowerCase()}
              </button>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Copy path button */}
      <button
        onClick={copyPathToClipboard}
        className="flex items-center justify-center w-8 h-8 border border-nav-border rounded text-nav-text-dim hover:text-nav-text hover:bg-nav-hover transition-all duration-200 hover:scale-110 group"
        title="Copy path to clipboard"
      >
        {copied ? (
          <span className="font-terminal text-xs text-green-400">✓</span>
        ) : (
          <span className="font-terminal text-xs group-hover:scale-110 transition-transform">
            📋
          </span>
        )}
      </button>

      {/* Path indicator for screen readers */}
      <div className="sr-only">
        Current path: {breadcrumbs.map(crumb => crumb.label).join(' > ')}
      </div>
    </div>
  );
} 