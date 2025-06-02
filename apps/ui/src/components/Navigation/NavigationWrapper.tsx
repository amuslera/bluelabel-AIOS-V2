import React from 'react';
import { useNavigationStore } from '../../store/navigationStore';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { CommandPalette } from './CommandPalette';

interface NavigationWrapperProps {
  children: React.ReactNode;
  className?: string;
}

export function NavigationWrapper({ children, className = '' }: NavigationWrapperProps) {
  const { isCollapsed } = useNavigationStore();

  return (
    <div className={`min-h-screen bg-terminal-bg text-terminal-cyan ${className}`}>
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content Area - Fix with explicit responsive classes */}
      <div className={`transition-all duration-200 ease-out ${
        isCollapsed ? 'lg:ml-16' : 'lg:ml-60'
      }`}>
        {/* Top Navigation Bar */}
        <TopBar />
        
        {/* Page Content with proper padding */}
        <main className="relative">
          {children}
        </main>
      </div>
      
      {/* Command Palette Overlay */}
      <CommandPalette />
    </div>
  );
} 