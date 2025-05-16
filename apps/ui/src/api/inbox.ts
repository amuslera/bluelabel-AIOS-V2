import { apiClient } from './client';

export interface EmailMessage {
  id: string;
  sender: string;
  subject: string;
  timestamp: string;
  content: string;
  status: 'unread' | 'read' | 'processed' | 'processing';
  codeword?: string;
}

export const inboxAPI = {
  // Get all messages
  getMessages: async (): Promise<EmailMessage[]> => {
    const { data } = await apiClient.get('/api/v1/communication/inbox');
    return data;
  },

  // Get single message
  getMessage: async (id: string): Promise<EmailMessage> => {
    const { data } = await apiClient.get(`/api/v1/communication/inbox/${id}`);
    return data;
  },

  // Mark message as read
  markAsRead: async (id: string): Promise<void> => {
    await apiClient.patch(`/api/v1/communication/inbox/${id}/read`);
  },

  // Process message
  processMessage: async (id: string): Promise<void> => {
    await apiClient.post(`/api/v1/communication/inbox/${id}/process`);
  },

  // Get inbox stats
  getStats: async (): Promise<{
    unread: number;
    processing: number;
    processed: number;
    total: number;
  }> => {
    const { data } = await apiClient.get('/api/v1/communication/inbox/stats');
    return data;
  },
};