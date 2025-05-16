/**
 * WebSocket connection status indicator
 */

import React from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';

interface WebSocketIndicatorProps {
  compact?: boolean;
}

export const WebSocketIndicator: React.FC<WebSocketIndicatorProps> = ({ compact = false }) => {
  const { isConnected, connectionState } = useWebSocket({ autoConnect: false });

  const statusColor = () => {
    switch (connectionState) {
      case 'connected':
        return 'bg-terminal-green';
      case 'connecting':
        return 'bg-terminal-yellow animate-pulse';
      case 'disconnected':
      case 'closed':
        return 'bg-terminal-red/50'; // Made less prominent
      case 'error':
        return 'bg-terminal-red/50'; // Made less prominent
      default:
        return 'bg-gray-500';
    }
  };

  const statusText = () => {
    switch (connectionState) {
      case 'connected':
        return 'LIVE';
      case 'connecting':
        return 'CONNECTING';
      case 'disconnected':
      case 'closed':
        return 'OFFLINE';
      case 'error':
        return 'OFFLINE'; // Changed from ERROR to OFFLINE
      default:
        return '';
    }
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${statusColor()}`} />
        {!compact && (
          <span className="text-xs font-mono text-terminal-cyan">
            {statusText()}
          </span>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 px-3 py-1 bg-terminal-bg/50 border border-terminal-cyan/20 rounded">
      <div className={`w-2 h-2 rounded-full ${statusColor()}`} />
      <span className="text-xs font-mono text-terminal-cyan/70">
        {statusText()}
      </span>
    </div>
  );
};