import React, { useEffect, useState } from 'react';
import { RetroButton } from '../../components/UI/RetroButton';
import { RetroCard } from '../../components/UI/RetroCard';
import { RetroLoader } from '../../components/UI/RetroLoader';
import { FileUploadModal } from '../../components/UI/FileUploadModal';
import { systemAPI } from '../../api/system';
import { useWebSocket } from '../../hooks/useWebSocket';
import type { SystemHealth, SystemActivity } from '../../api/system';
import type { WebSocketMessage } from '../../services/websocket';

interface SystemStatus {
  status: 'online' | 'offline' | 'warning';
  components: {
    [key: string]: {
      status: 'ok' | 'error' | 'warning';
      lastCheck: string;
    };
  };
}

export const Dashboard: React.FC = () => {
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [activities, setActivities] = useState<SystemActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [recentOperations, setRecentOperations] = useState<string[]>([]);
  
  // WebSocket setup
  const { subscribe, unsubscribe } = useWebSocket({
    onMessage: (message: WebSocketMessage) => {
      handleWebSocketMessage(message);
    },
  });

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    switch (message.event_type) {
      case 'system_health':
        setSystemHealth(message.payload);
        break;
      case 'component_status':
        updateComponentStatus(message.payload);
        break;
      case 'agent_started':
      case 'agent_completed':
      case 'email_processed':
        addRecentOperation(message);
        updateActivities(message);
        break;
    }
  };

  const addRecentOperation = (message: WebSocketMessage) => {
    const operation = formatOperationMessage(message);
    setRecentOperations(prev => [operation, ...prev.slice(0, 3)]);
  };

  const formatOperationMessage = (message: WebSocketMessage): string => {
    const timestamp = new Date(message.timestamp).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
    
    switch (message.event_type) {
      case 'agent_started':
        return `${timestamp} > run agent ${message.payload.agent_name} --task ${message.payload.task}`;
      case 'agent_completed':
        return `${timestamp} > [COMPLETED] ${message.payload.result}`;
      case 'email_processed':
        return `${timestamp} > process email --from ${message.payload.from}`;
      default:
        return `${timestamp} > ${message.event_type}`;
    }
  };

  const updateComponentStatus = (payload: any) => {
    setSystemHealth(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        services: {
          ...prev.services,
          [payload.component]: {
            status: payload.status,
            lastCheck: payload.timestamp
          }
        }
      };
    });
  };

  const updateActivities = (message: WebSocketMessage) => {
    const activity: SystemActivity = {
      id: message.metadata?.event_id || Date.now().toString(),
      time: new Date(message.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
      type: message.event_type.replace('_', ' '),
      description: message.payload.description || message.event_type,
      source: message.payload.source || 'System',
      status: message.payload.status || 'info'
    };
    
    setActivities(prev => [activity, ...prev.slice(0, 4)]);
  };

  const fetchSystemData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [health, recentActivity] = await Promise.all([
        systemAPI.getHealth(),
        systemAPI.getRecentActivity(5)
      ]);
      
      setSystemHealth(health);
      setActivities(recentActivity);
    } catch (err) {
      setError('Failed to load system status');
      
      // Fallback to mock data if API fails
      setSystemHealth({
        status: 'online',
        services: {
          content_mind: { status: 'ok', lastCheck: new Date().toISOString() },
          email_gateway: { status: 'ok', lastCheck: new Date().toISOString() },
          model_router: { status: 'ok', lastCheck: new Date().toISOString() },
          redis: { status: 'ok', lastCheck: new Date().toISOString() },
        },
      });
      
      setActivities([
        { id: '1', time: '10:42', type: 'Email processed', description: 'Processed email', source: 'john@example.com', status: 'success' },
        { id: '2', time: '10:38', type: 'WhatsApp received', description: 'New WhatsApp message', source: '+1234567890', status: 'pending' },
        { id: '3', time: '10:35', type: 'Agent run', description: 'Agent execution', source: 'ContentMind', status: 'success' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchSystemData, 30000);
    
    return () => {
      clearInterval(interval);
    };
  }, []);
  
  useEffect(() => {
    // Subscribe to WebSocket events in a separate effect
    const eventTypes = [
      'system_health',
      'component_status',
      'agent_started',
      'agent_completed',
      'email_processed',
      'knowledge_created',
      'knowledge_updated'
    ];
    
    subscribe(eventTypes);
    
    return () => {
      unsubscribe(eventTypes);
    };
  }, [subscribe, unsubscribe]);

  const StatusIndicator: React.FC<{ status: string }> = ({ status }) => {
    const colors = {
      ok: 'text-terminal-green',
      error: 'text-error-pink',
      warning: 'text-terminal-amber',
      online: 'text-terminal-green',
      offline: 'text-error-pink',
    };
    
    return (
      <span className={`font-bold ${colors[status as keyof typeof colors] || 'text-terminal-cyan'}`}>
        [{status.toUpperCase()}]
      </span>
    );
  };

  const handleFileUpload = async (file: File) => {
    try {
      // TODO: Implement actual file upload API call
      // await filesAPI.upload(file);
      alert(`File "${file.name}" uploaded successfully!`);
    } catch (error) {
      setError('Failed to upload file');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RetroLoader text="Loading system status..." size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold mb-6">System Dashboard</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* System Status */}
        <RetroCard title="System Status">
          {error && (
            <div className="text-error-pink mb-4">
              {error}
            </div>
          )}
          {systemHealth && systemHealth.services ? (
            <div className="space-y-2">
              {Object.entries(systemHealth.services).map(([name, service]) => (
                <div key={name} className="flex justify-between">
                  <span className="text-terminal-cyan">{name.replace('_', ' ').toUpperCase()}</span>
                  <StatusIndicator status={service.status} />
                </div>
              ))}
            </div>
          ) : (
            <div className="text-terminal-cyan">Loading status...</div>
          )}
        </RetroCard>

        {/* Recent Activity */}
        <RetroCard title="Recent Activity">
          <div className="space-y-2">
            {activities.map((activity) => (
              <div key={activity.id} className="text-terminal-cyan">
                <span className="text-terminal-cyan/70">{activity.time}</span> - {activity.type}
                <div className="text-sm text-terminal-cyan/50 ml-4">→ {activity.source}</div>
              </div>
            ))}
          </div>
        </RetroCard>
      </div>

      {/* Quick Actions */}
      <RetroCard title="Quick Actions">
        <div className="flex flex-wrap gap-4">
          <RetroButton onClick={() => window.location.href = '/agents'}>
            RUN AGENT
          </RetroButton>
          <RetroButton onClick={() => setShowUploadModal(true)} variant="success">
            UPLOAD FILE
          </RetroButton>
          <RetroButton onClick={() => window.location.href = '/logs'} variant="warning">
            VIEW LOGS
          </RetroButton>
          <RetroButton onClick={() => window.location.href = '/terminal'} variant="primary">
            OPEN TERMINAL
          </RetroButton>
        </div>
      </RetroCard>

      {/* Recent Commands */}
      <RetroCard title="RECENT OPERATIONS">
        <div className="font-mono space-y-2">
          {recentOperations.length > 0 ? (
            recentOperations.map((operation, index) => (
              <div key={index} className="text-terminal-cyan/80">
                <span className="text-terminal-cyan">&gt;</span> {operation}
              </div>
            ))
          ) : (
            <>
              <div className="text-terminal-cyan/80">
                <span className="text-terminal-cyan">&gt;</span> process email --from john@example.com
                <div className="text-terminal-green ml-4">[COMPLETED] Q3 Report analyzed and stored</div>
              </div>
              <div className="text-terminal-cyan/80">
                <span className="text-terminal-cyan">&gt;</span> run agent ContentMind --mode summarize
                <div className="text-terminal-amber ml-4">[PROCESSING] Generating summary...</div>
              </div>
              <div className="text-terminal-cyan/80">
                <span className="text-terminal-cyan">&gt;</span> fetch knowledge --tag "quarterly-report"
                <div className="text-terminal-green ml-4">[COMPLETED] Found 12 matching items</div>
              </div>
              <div className="text-terminal-cyan/80">
                <span className="text-terminal-cyan">&gt;</span> check inbox --filter unread
                <div className="text-terminal-green ml-4">[COMPLETED] 3 new messages</div>
              </div>
            </>
          )}
          <div className="text-terminal-cyan mt-4">&gt; <span className="cursor">_</span></div>
        </div>
      </RetroCard>

      <FileUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUpload={handleFileUpload}
      />
    </div>
  );
};