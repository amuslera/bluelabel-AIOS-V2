export interface SystemStatus {
  status: 'online' | 'offline' | 'warning';
  components: {
    [key: string]: {
      status: 'ok' | 'error' | 'warning';
      lastCheck: string;
    };
  };
}

export interface InboxItem {
  id: string;
  type: 'email' | 'whatsapp' | 'manual';
  from: string;
  subject: string;
  time: string;
  status: 'pending' | 'processing' | 'complete' | 'failed';
  hasCodeword?: boolean;
}

export interface KnowledgeItem {
  id: string;
  title: string;
  type: string;
  source: string;
  created: string;
  tags: string[];
  preview: string;
}

export interface Agent {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'error';
  lastActivity: string;
  tasksCompleted: number;
  tasksFailed: number;
  averageProcessingTime: number;
}
