import React from 'react';
import { useNavigationStore } from '../../store/navigationStore';

// Compact sidebar logo component
const SidebarLogo: React.FC<{ isCollapsed: boolean }> = ({ isCollapsed }) => {
  if (isCollapsed) {
    // Collapsed state - show just initials
    return (
      <div className="flex items-center justify-center w-8 h-8 bg-terminal-cyan text-terminal-bg rounded border border-terminal-cyan">
        <span className="font-terminal text-sm font-bold">BL</span>
      </div>
    );
  }

  // Expanded state - show compact logo
  return (
    <div className="flex items-center space-x-2">
      <div className="flex items-center justify-center w-8 h-8 bg-terminal-cyan text-terminal-bg rounded border border-terminal-cyan">
        <span className="font-terminal text-sm font-bold">BL</span>
      </div>
      <div className="flex flex-col">
        <span className="text-terminal-cyan font-terminal text-sm font-bold leading-none">
          BLUELABEL
        </span>
        <span className="text-terminal-cyan/70 font-terminal text-xs leading-none">
          AIOS V2
        </span>
      </div>
    </div>
  );
};

export function SidebarHeader() {
  const { isCollapsed, toggleSidebar } = useNavigationStore();

  return (
    <div className="flex items-center justify-between p-4 border-b border-nav-border bg-nav-bg">
      {/* Logo Section */}
      <div className={`flex items-center transition-all duration-200 ${
        isCollapsed ? 'justify-center w-full' : 'space-x-3'
      }`}>
        <SidebarLogo isCollapsed={isCollapsed} />
        
        {!isCollapsed && (
          <div className="flex flex-col">
            <span className="text-nav-text font-terminal text-xs uppercase tracking-wider">
              SYSTEM READY
            </span>
          </div>
        )}
      </div>

      {/* Collapse Toggle - Hidden on mobile, only show on desktop */}
      {!isCollapsed && (
        <button
          onClick={toggleSidebar}
          className="hidden lg:flex items-center justify-center w-8 h-8 rounded border border-nav-border text-nav-text hover:bg-nav-hover hover:text-terminal-cyan transition-all duration-200 hover:scale-110"
          title="Collapse sidebar"
          aria-label="Collapse sidebar"
        >
          <span className="text-sm font-terminal">‹</span>
        </button>
      )}
      
      {/* Expand Toggle - Only show when collapsed on desktop */}
      {isCollapsed && (
        <button
          onClick={toggleSidebar}
          className="hidden lg:flex absolute right-2 items-center justify-center w-6 h-6 rounded border border-nav-border text-nav-text hover:bg-nav-hover hover:text-terminal-cyan transition-all duration-200 hover:scale-110"
          title="Expand sidebar"
          aria-label="Expand sidebar"
        >
          <span className="text-sm font-terminal">›</span>
        </button>
      )}
    </div>
  );
} 