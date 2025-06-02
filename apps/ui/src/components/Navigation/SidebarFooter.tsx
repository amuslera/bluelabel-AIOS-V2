import React from 'react';
import { useNavigationStore } from '../../store/navigationStore';
import { WebSocketIndicator } from '../UI/WebSocketIndicator';

export function SidebarFooter() {
  const { isCollapsed } = useNavigationStore();

  return (
    <div className="border-t border-nav-border bg-nav-bg">
      {/* System Status */}
      <div className={`p-3 ${isCollapsed ? 'px-2' : ''} transition-all duration-200`}>
        {!isCollapsed ? (
          <div className="space-y-2">
            {/* WebSocket Status */}
            <div className="flex items-center justify-between">
              <span className="text-nav-text-dim font-terminal text-xs uppercase">
                Connection
              </span>
              <WebSocketIndicator />
            </div>
            
            {/* System Status */}
            <div className="flex items-center justify-between">
              <span className="text-nav-text-dim font-terminal text-xs uppercase">
                System
              </span>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-green-400 font-terminal text-xs">ONLINE</span>
              </div>
            </div>

            {/* Agent Status */}
            <div className="flex items-center justify-between">
              <span className="text-nav-text-dim font-terminal text-xs uppercase">
                Agents
              </span>
              <span className="text-terminal-cyan font-terminal text-xs">4/4</span>
            </div>

            {/* Version */}
            <div className="pt-2 border-t border-nav-border">
              <div className="flex items-center justify-between">
                <span className="text-nav-text-dim font-terminal text-xs">
                  AIOS v2.1.0
                </span>
                <span className="text-nav-text-dim font-terminal text-xs">
                  BUILD-{Math.floor(Date.now() / 1000).toString().slice(-4)}
                </span>
              </div>
            </div>
          </div>
        ) : (
          // Collapsed state - show minimal indicators
          <div className="flex flex-col items-center space-y-3">
            {/* Connection indicator */}
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" title="System Online" />
            
            {/* Agent count */}
            <div className="text-terminal-cyan font-terminal text-xs" title="4 agents active">
              4
            </div>
            
            {/* Version indicator */}
            <div className="text-nav-text-dim font-terminal text-xs rotate-90 origin-center" title="AIOS v2.1.0">
              v2
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions - Only show when expanded */}
      {!isCollapsed && (
        <div className="p-3 border-t border-nav-border/50">
          <div className="flex space-x-2">
            <button 
              className="flex-1 px-2 py-1 text-xs font-terminal text-nav-text-dim hover:text-nav-text border border-nav-border hover:border-terminal-cyan rounded transition-all duration-200 hover:scale-105"
              title="Quick restart"
            >
              ⟲ RESTART
            </button>
            <button 
              className="flex-1 px-2 py-1 text-xs font-terminal text-nav-text-dim hover:text-nav-text border border-nav-border hover:border-terminal-cyan rounded transition-all duration-200 hover:scale-105"
              title="System logs"
            >
              📋 LOGS
            </button>
          </div>
        </div>
      )}
    </div>
  );
} 