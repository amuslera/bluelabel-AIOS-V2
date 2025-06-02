import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';

interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: string;
  description?: string;
}

interface SidebarItemProps {
  item: NavItem;
  isActive: boolean;
  isCollapsed: boolean;
}

export function SidebarItem({ item, isActive, isCollapsed }: SidebarItemProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  const baseClasses = `
    group relative flex items-center w-full px-3 py-3 rounded-lg
    font-terminal text-sm transition-all duration-200 ease-out
    hover:scale-102 hover:shadow-md
  `;

  const activeClasses = isActive
    ? 'bg-nav-active text-terminal-cyan border border-nav-border shadow-lg scale-105'
    : 'text-nav-text-dim hover:bg-nav-hover hover:text-nav-text border border-transparent hover:border-nav-border';

  const handleMouseEnter = () => {
    if (isCollapsed) {
      setShowTooltip(true);
    }
  };

  const handleMouseLeave = () => {
    setShowTooltip(false);
  };

  return (
    <div className="relative">
      <NavLink
        to={item.path}
        className={`${baseClasses} ${activeClasses}`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        title={isCollapsed ? item.label : undefined}
      >
        {/* Icon */}
        <div className={`flex items-center justify-center ${
          isCollapsed ? 'w-full' : 'w-6 mr-3'
        } transition-all duration-200`}>
          <span className={`text-lg ${isActive ? 'animate-pulse' : ''}`}>
            {item.icon}
          </span>
        </div>

        {/* Label - Hidden when collapsed */}
        {!isCollapsed && (
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="uppercase tracking-wide truncate">
                [{item.label}]
              </span>
              {isActive && (
                <span className="text-terminal-cyan text-xs animate-pulse">
                  ●
                </span>
              )}
            </div>
            {item.description && !isActive && (
              <div className="text-xs text-nav-text-dim mt-1 truncate">
                {item.description}
              </div>
            )}
          </div>
        )}

        {/* Active indicator bar */}
        {isActive && (
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-terminal-cyan rounded-r animate-pulse" />
        )}
      </NavLink>

      {/* Tooltip for collapsed state */}
      {isCollapsed && showTooltip && (
        <div className="absolute left-full top-1/2 transform -translate-y-1/2 ml-2 z-50">
          <div className="bg-nav-bg border border-nav-border rounded-lg px-3 py-2 shadow-lg min-w-max">
            <div className="text-nav-text font-terminal text-sm uppercase tracking-wide">
              [{item.label}]
            </div>
            {item.description && (
              <div className="text-nav-text-dim text-xs mt-1">
                {item.description}
              </div>
            )}
            {/* Arrow pointer */}
            <div className="absolute right-full top-1/2 transform -translate-y-1/2">
              <div className="w-0 h-0 border-t-4 border-b-4 border-r-4 border-transparent border-r-nav-border"></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 