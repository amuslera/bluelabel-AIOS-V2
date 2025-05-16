/**
 * Application configuration
 */

export const appConfig = {
  // API configuration
  api: {
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
    timeout: 30000,
  },
  
  // WebSocket configuration
  websocket: {
    enabled: process.env.REACT_APP_WEBSOCKET_ENABLED === 'true' || false,
    url: process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8001/ws',
    autoReconnect: false,
  },
  
  // UI configuration
  ui: {
    refreshInterval: 30000, // 30 seconds
  }
};