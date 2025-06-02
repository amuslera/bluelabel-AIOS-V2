import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useNavigationStore } from '../../store/navigationStore';
import { SidebarHeader } from './SidebarHeader';
import { SidebarItem } from './SidebarItem';
import { SidebarFooter } from './SidebarFooter';

interface SidebarProps {
  className?: string;
}

interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: string;
  description?: string;
}

const navItems: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    path: '/',
    icon: '◉',
    description: 'System overview and status'
  },
  {
    id: 'inbox',
    label: 'Inbox',
    path: '/inbox',
    icon: '📧',
    description: 'Messages and notifications'
  },
  {
    id: 'knowledge',
    label: 'Knowledge',
    path: '/knowledge',
    icon: '📚',
    description: 'Knowledge base and documents'
  },
  {
    id: 'agents',
    label: 'Agents',
    path: '/agents',
    icon: '🤖',
    description: 'AI agents and automation'
  },
  {
    id: 'terminal',
    label: 'Terminal',
    path: '/terminal',
    icon: '⌘',
    description: 'Command line interface'
  },
  {
    id: 'logs',
    label: 'Logs',
    path: '/logs',
    icon: '📝',
    description: 'System logs and history'
  },
  {
    id: 'settings',
    label: 'Settings',
    path: '/settings',
    icon: '⚙️',
    description: 'System configuration'
  }
];

export function Sidebar({ className = '' }: SidebarProps) {
  const location = useLocation();
  const { 
    isCollapsed, 
    isMobileMenuOpen, 
    setActiveRoute,
    setMobileMenuOpen 
  } = useNavigationStore();

  // Update active route when location changes
  useEffect(() => {
    setActiveRoute(location.pathname);
  }, [location.pathname, setActiveRoute]);

  // Close mobile menu when route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname, setMobileMenuOpen]);

  const sidebarClasses = `
    fixed left-0 top-0 h-full z-50 transition-all duration-200 ease-out
    bg-nav-bg border-r border-nav-border
    ${isCollapsed ? 'w-16' : 'w-60'}
    ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
    lg:translate-x-0
    ${className}
  `;

  return (
    <>
      {/* Mobile backdrop */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <div className={sidebarClasses}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <SidebarHeader />
          
          {/* Navigation Items */}
          <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
            {navItems.map((item) => (
              <SidebarItem
                key={item.id}
                item={item}
                isActive={location.pathname === item.path}
                isCollapsed={isCollapsed}
              />
            ))}
          </nav>
          
          {/* Footer */}
          <SidebarFooter />
        </div>
      </div>
    </>
  );
} 