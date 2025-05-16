import { apiClient } from './client';

export interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'inactive' | 'error';
  lastRun?: string;
  metrics?: {
    successRate: number;
    avgExecutionTime: number;
    totalExecutions: number;
  };
}

export interface AgentExecution {
  agentId: string;
  input: any;
  output?: any;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime: string;
  endTime?: string;
  error?: string;
}

export const agentsAPI = {
  // Get all agents
  getAgents: async (): Promise<Agent[]> => {
    const { data } = await apiClient.get('/api/v1/agents');
    return data;
  },

  // Execute agent
  executeAgent: async (
    agentId: string,
    input: any
  ): Promise<AgentExecution> => {
    const { data } = await apiClient.post(`/api/v1/agents/${agentId}/execute`, input);
    return data;
  },

  // Get agent status
  getAgentStatus: async (agentId: string): Promise<Agent> => {
    const { data } = await apiClient.get(`/api/v1/agents/${agentId}`);
    return data;
  },

  // Get agent metrics
  getAgentMetrics: async (agentId: string): Promise<any> => {
    const { data } = await apiClient.get(`/api/v1/agents/${agentId}/metrics`);
    return data;
  },
};