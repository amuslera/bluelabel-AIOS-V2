import { apiClient } from './client';

export interface SystemHealth {
  status: 'online' | 'degraded' | 'offline';
  services: {
    [key: string]: {
      status: 'ok' | 'error' | 'warning';
      lastCheck: string;
      message?: string;
    };
  };
}

export interface SystemActivity {
  id: string;
  time: string;
  type: string;
  description: string;
  source: string;
  status?: 'success' | 'error' | 'pending';
}

export const systemAPI = {
  // Get system health
  getHealth: async (): Promise<SystemHealth> => {
    const { data } = await apiClient.get('/health');
    return data;
  },

  // Get recent activity
  getRecentActivity: async (limit: number = 10): Promise<SystemActivity[]> => {
    const { data } = await apiClient.get('/api/v1/system/activity', {
      params: { limit },
    });
    return data;
  },

  // Get system statistics
  getStats: async (): Promise<any> => {
    const { data } = await apiClient.get('/api/v1/system/stats');
    return data;
  },

  // Run system command (for terminal)
  runCommand: async (command: string): Promise<{
    output: string;
    error?: string;
    exitCode: number;
  }> => {
    const { data } = await apiClient.post('/api/v1/system/command', { command });
    return data;
  },
};