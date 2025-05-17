import React from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';

export const WebSocketIndicator: React.FC = () => {
  const { connectionState } = useWebSocket();
  const connectionStatus = connectionState;
  const isConnected = connectionStatus === 'connected';

  return (
    <div className="flex items-center space-x-2">
      <div className={`w-3 h-3 rounded-full ${
        connectionStatus === 'connected' ? 'bg-green-400' : 
        connectionStatus === 'connecting' ? 'bg-yellow-400 animate-pulse' : 
        'bg-red-400'
      }`} />
      <span className="text-xs text-cyan-400 uppercase">
        {connectionStatus}
      </span>
    </div>
  );
};