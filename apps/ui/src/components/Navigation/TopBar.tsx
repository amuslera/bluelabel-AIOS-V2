import React, { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { useNavigationStore, generateBreadcrumbs } from '../../store/navigationStore';
import { Breadcrumbs } from './Breadcrumbs';
import { WebSocketIndicator } from '../UI/WebSocketIndicator';

export function TopBar() {
  const location = useLocation();
  const { 
    isCollapsed,
    isMobileMenuOpen,
    toggleMobileMenu,
    toggleCommandPalette,
    updateBreadcrumbs 
  } = useNavigationStore();

  // Update breadcrumbs when route changes
  useEffect(() => {
    const breadcrumbs = generateBreadcrumbs(location.pathname);
    updateBreadcrumbs(breadcrumbs);
  }, [location.pathname, updateBreadcrumbs]);

  const handleCommandPalette = useCallback(() => {
    toggleCommandPalette();
  }, [toggleCommandPalette]);

  // Keyboard shortcut for command palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        handleCommandPalette();
      }
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        e.preventDefault();
        // Only toggle sidebar on desktop
        if (window.innerWidth >= 1024) {
          useNavigationStore.getState().toggleSidebar();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleCommandPalette]);

  return (
    <div className={`sticky top-0 z-40 bg-terminal-bg border-b border-nav-border backdrop-blur-sm transition-all duration-200 ${
      isCollapsed ? 'lg:ml-16' : 'lg:ml-60'
    }`}>
      <div className="px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Left Section: Mobile Menu + Breadcrumbs */}
          <div className="flex items-center space-x-4 flex-1 min-w-0">
            {/* Mobile Hamburger Menu */}
            <button
              onClick={toggleMobileMenu}
              className="lg:hidden flex items-center justify-center w-10 h-10 border border-nav-border rounded-lg text-nav-text hover:bg-nav-hover hover:text-terminal-cyan transition-all duration-200"
              aria-label="Toggle mobile menu"
            >
              <div className="flex flex-col space-y-1">
                <div className={`w-4 h-0.5 bg-current transition-all duration-200 ${
                  isMobileMenuOpen ? 'rotate-45 translate-y-1.5' : ''
                }`} />
                <div className={`w-4 h-0.5 bg-current transition-all duration-200 ${
                  isMobileMenuOpen ? 'opacity-0' : ''
                }`} />
                <div className={`w-4 h-0.5 bg-current transition-all duration-200 ${
                  isMobileMenuOpen ? '-rotate-45 -translate-y-1.5' : ''
                }`} />
              </div>
            </button>

            {/* Breadcrumbs */}
            <div className="flex-1 min-w-0">
              <Breadcrumbs />
            </div>
          </div>

          {/* Right Section: Actions */}
          <div className="flex items-center space-x-3">
            {/* Command Palette Trigger */}
            <button
              onClick={handleCommandPalette}
              className="hidden sm:flex items-center space-x-2 px-3 py-2 border border-nav-border rounded-lg text-nav-text-dim hover:text-nav-text hover:bg-nav-hover transition-all duration-200 hover:scale-105"
              title="Open command palette (Ctrl+K)"
            >
              <span className="font-terminal text-sm">⌘</span>
              <span className="font-terminal text-xs uppercase">Search</span>
              <div className="flex space-x-1">
                <kbd className="px-1 py-0.5 text-xs font-terminal bg-nav-bg border border-nav-border rounded">
                  ⌃
                </kbd>
                <kbd className="px-1 py-0.5 text-xs font-terminal bg-nav-bg border border-nav-border rounded">
                  K
                </kbd>
              </div>
            </button>

            {/* Mobile Command Palette */}
            <button
              onClick={handleCommandPalette}
              className="sm:hidden flex items-center justify-center w-10 h-10 border border-nav-border rounded-lg text-nav-text hover:bg-nav-hover hover:text-terminal-cyan transition-all duration-200"
              title="Open command palette"
            >
              <span className="font-terminal text-lg">⌘</span>
            </button>

            {/* WebSocket Indicator */}
            <div className="hidden md:block">
              <WebSocketIndicator />
            </div>

            {/* User Menu */}
            <div className="relative">
              <button className="flex items-center space-x-2 px-3 py-2 border border-nav-border rounded-lg text-nav-text hover:bg-nav-hover hover:text-terminal-cyan transition-all duration-200 hover:scale-105">
                <div className="w-6 h-6 bg-terminal-cyan rounded border border-nav-border flex items-center justify-center">
                  <span className="font-terminal text-xs text-black">CA</span>
                </div>
                <span className="hidden md:inline font-terminal text-sm uppercase">
                  Agent
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 