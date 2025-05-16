/**
 * WebSocket service for real-time updates
 */

import { EventEmitter } from 'events';

export interface WebSocketMessage {
  event_type: string;
  timestamp: string;
  payload: any;
  metadata?: {
    event_id: string;
    tenant_id?: string;
    correlation_id?: string;
  };
}

class WebSocketService extends EventEmitter {
  private socket: WebSocket | null = null;
  private reconnectInterval: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private autoReconnect = false; // Disable auto-reconnect by default

  constructor() {
    super();
    this.setMaxListeners(20); // Increase max listeners for multiple components
  }

  connect(url: string = 'ws://localhost:8001/ws', enableAutoReconnect: boolean = false) {
    this.autoReconnect = enableAutoReconnect;
    
    if (this.socket?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      this.socket = new WebSocket(url);
    } catch (error) {
      this.emit('error', error);
      return;
    }

    this.socket.onopen = () => {
      this.emit('connected');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      
      // Send initial authentication/subscription message
      this.send({
        event_type: 'subscribe',
        timestamp: new Date().toISOString(),
        payload: {
          channels: ['system', 'agents', 'communication', 'knowledge']
        }
      });
    };

    this.socket.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        
        // Emit specific events based on message type
        this.emit('message', message);
        this.emit(message.event_type, message.payload);
        
        // Handle specific event types
        switch (message.event_type) {
          case 'agent_started':
          case 'agent_completed':
          case 'agent_failed':
            this.emit('agent_update', message);
            break;
          case 'email_received':
          case 'email_processed':
            this.emit('communication_update', message);
            break;
          case 'knowledge_created':
          case 'knowledge_updated':
            this.emit('knowledge_update', message);
            break;
          case 'system_health':
          case 'component_status':
            this.emit('system_update', message);
            break;
        }
      } catch (error) {
        // Silently handle parsing errors
      }
    };

    this.socket.onerror = (error) => {
      this.emit('error', error);
    };

    this.socket.onclose = () => {
      this.emit('disconnected');
      if (this.autoReconnect) {
        this.attemptReconnect();
      }
    };
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.emit('reconnect_failed');
      return;
    }

    this.reconnectAttempts++;
    
    this.reconnectInterval = setTimeout(() => {
      this.connect();
    }, this.reconnectDelay);

    // Exponential backoff
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000); // Max 30 seconds
  }

  disconnect() {
    if (this.reconnectInterval) {
      clearTimeout(this.reconnectInterval);
      this.reconnectInterval = null;
    }

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  send(message: Partial<WebSocketMessage>) {
    if (this.socket?.readyState !== WebSocket.OPEN) {
      return false;
    }

    const fullMessage: WebSocketMessage = {
      event_type: message.event_type || 'unknown',
      timestamp: message.timestamp || new Date().toISOString(),
      payload: message.payload || {},
      metadata: {
        event_id: message.metadata?.event_id || Date.now().toString(),
        ...message.metadata
      }
    };

    this.socket.send(JSON.stringify(fullMessage));
    return true;
  }

  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  getConnectionState(): string {
    if (!this.socket) return 'disconnected';
    
    switch (this.socket.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'closed';
      default:
        return 'unknown';
    }
  }
}

// Create singleton instance
export const websocketService = new WebSocketService();

// Export types for components
export type { WebSocketService };