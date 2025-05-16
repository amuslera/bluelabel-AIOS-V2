/**
 * Custom hook for WebSocket integration
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { websocketService, WebSocketMessage } from '../services/websocket';
import { appConfig } from '../config/app.config';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  url?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: any) => void;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    autoConnect = false, // Changed default to false to prevent automatic connection
    url,
    onMessage,
    onConnect,
    onDisconnect,
    onError
  } = options;

  const [isConnected, setIsConnected] = useState(websocketService.isConnected());
  const [connectionState, setConnectionState] = useState(websocketService.getConnectionState());
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const subscribersRef = useRef<Set<string>>(new Set());

  // Handle connection state changes
  const handleConnected = useCallback(() => {
    setIsConnected(true);
    setConnectionState('connected');
    onConnect?.();
  }, [onConnect]);

  const handleDisconnected = useCallback(() => {
    setIsConnected(false);
    setConnectionState('disconnected');
    onDisconnect?.();
  }, [onDisconnect]);

  const handleError = useCallback((error: any) => {
    setConnectionState('error');
    onError?.(error);
  }, [onError]);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    setLastMessage(message);
    onMessage?.(message);
  }, [onMessage]);

  // Subscribe to specific event types
  const subscribe = useCallback((eventTypes: string | string[]) => {
    if (!appConfig.websocket.enabled) {
      return;
    }
    
    const types = Array.isArray(eventTypes) ? eventTypes : [eventTypes];
    
    types.forEach(type => {
      if (!subscribersRef.current.has(type)) {
        subscribersRef.current.add(type);
        websocketService.on(type, handleMessage);
      }
    });
  }, [handleMessage]);

  // Unsubscribe from specific event types
  const unsubscribe = useCallback((eventTypes: string | string[]) => {
    const types = Array.isArray(eventTypes) ? eventTypes : [eventTypes];
    
    types.forEach(type => {
      if (subscribersRef.current.has(type)) {
        subscribersRef.current.delete(type);
        websocketService.off(type, handleMessage);
      }
    });
  }, [handleMessage]);

  // Send a message
  const sendMessage = useCallback((message: Partial<WebSocketMessage>) => {
    return websocketService.send(message);
  }, []);

  // Connect/disconnect functions
  const connect = useCallback(() => {
    if (appConfig.websocket.enabled) {
      websocketService.connect(url || appConfig.websocket.url, appConfig.websocket.autoReconnect);
    }
  }, [url]);

  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  // Setup effect
  useEffect(() => {
    // Only proceed if WebSocket is enabled in config
    if (!appConfig.websocket.enabled) {
      return;
    }
    
    // Add event listeners
    websocketService.on('connected', handleConnected);
    websocketService.on('disconnected', handleDisconnected);
    websocketService.on('error', handleError);
    websocketService.on('message', handleMessage);

    // Auto-connect if enabled
    if (autoConnect && !websocketService.isConnected()) {
      connect();
    }

    // Cleanup
    return () => {
      websocketService.off('connected', handleConnected);
      websocketService.off('disconnected', handleDisconnected);
      websocketService.off('error', handleError);
      websocketService.off('message', handleMessage);

      // Unsubscribe from all event types
      subscribersRef.current.forEach(type => {
        websocketService.off(type, handleMessage);
      });
      subscribersRef.current.clear();
    };
  }, [autoConnect, connect, handleConnected, handleDisconnected, handleError, handleMessage]);

  return {
    isConnected,
    connectionState,
    lastMessage,
    connect,
    disconnect,
    sendMessage,
    subscribe,
    unsubscribe
  };
};