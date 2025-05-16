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

  // Get recent activity - using analytics summary as proxy
  getRecentActivity: async (limit: number = 10): Promise<SystemActivity[]> => {
    try {
      // Use analytics summary endpoint as a proxy for activity
      const { data } = await apiClient.get('/api/v1/status/analytics/summary', {
        params: { days: 1 },
      });
      
      // Convert analytics data to activity format
      const activities: SystemActivity[] = [];
      
      if (data.files_processed > 0) {
        activities.push({
          id: '1',
          time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
          type: 'Files Processed',
          description: `${data.files_processed} files processed today`,
          source: 'File System',
          status: 'success'
        });
      }
      
      if (data.digests_generated > 0) {
        activities.push({
          id: '2',
          time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
          type: 'Digests Generated',
          description: `${data.digests_generated} digests created today`,
          source: 'Digest System',
          status: 'success'
        });
      }
      
      return activities.slice(0, limit);
    } catch (error) {
      console.error('Failed to fetch activities:', error);
      return [];
    }
  },

  // Get system statistics - using analytics summary
  getStats: async (): Promise<any> => {
    try {
      const { data } = await apiClient.get('/api/v1/status/analytics/summary', {
        params: { days: 7 },
      });
      return data;
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      return {};
    }
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