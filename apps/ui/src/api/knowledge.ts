import { apiClient } from './client';

export interface KnowledgeItem {
  id: string;
  title: string;
  type: 'document' | 'article' | 'email' | 'note';
  source: string;
  timestamp: string;
  summary: string;
  tags: string[];
  processedBy: string;
}

export const knowledgeAPI = {
  // Get all knowledge items
  getItems: async (params?: {
    search?: string;
    tag?: string;
    type?: string;
  }): Promise<KnowledgeItem[]> => {
    const { data } = await apiClient.get('/api/v1/knowledge/items', { params });
    return data;
  },

  // Get single item
  getItem: async (id: string): Promise<KnowledgeItem> => {
    const { data } = await apiClient.get(`/api/v1/knowledge/items/${id}`);
    return data;
  },

  // Create new item
  createItem: async (item: Partial<KnowledgeItem>): Promise<KnowledgeItem> => {
    const { data } = await apiClient.post('/api/v1/knowledge/items', item);
    return data;
  },

  // Export item
  exportItem: async (id: string, format: 'json' | 'pdf' | 'md'): Promise<Blob> => {
    const { data } = await apiClient.get(`/api/v1/knowledge/items/${id}/export`, {
      params: { format },
      responseType: 'blob',
    });
    return data;
  },

  // Get stats
  getStats: async (): Promise<{
    totalItems: number;
    documents: number;
    uniqueTags: number;
    agentsUsed: string[];
  }> => {
    const { data } = await apiClient.get('/api/v1/knowledge/stats');
    return data;
  },

  // Get all tags
  getTags: async (): Promise<string[]> => {
    const { data } = await apiClient.get('/api/v1/knowledge/tags');
    return data;
  },
};