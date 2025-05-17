import React, { useState } from 'react';
import { RetroButton } from '../../components/UI/RetroButton';
import { RetroCard } from '../../components/UI/RetroCard';
import { FileUploadModal } from '../../components/UI/FileUploadModal';

export const Dashboard: React.FC = () => {
  const [showUploadModal, setShowUploadModal] = useState(false);

  // Fixed default data
  const systemHealth = {
    status: 'online',
    services: {
      content_mind: { status: 'ok', lastCheck: new Date().toISOString() },
      email_gateway: { status: 'ok', lastCheck: new Date().toISOString() },
      model_router: { status: 'ok', lastCheck: new Date().toISOString() },
      redis: { status: 'ok', lastCheck: new Date().toISOString() },
    },
  };
  
  const activities = [
    { id: '1', time: '10:42', type: 'Email processed', description: 'Processed email', source: 'john@example.com', status: 'success' },
    { id: '2', time: '10:38', type: 'WhatsApp received', description: 'New WhatsApp message', source: '+1234567890', status: 'pending' },
    { id: '3', time: '10:35', type: 'Agent run', description: 'Agent execution', source: 'ContentMind', status: 'success' },
  ];
  
  const recentOperations = [
    '10:45 > process email --from john@example.com',
    '10:40 > run agent ContentMind --task analyze',
    '10:35 > fetch knowledge --tag "quarterly-report"',
    '10:30 > check inbox --filter unread'
  ];

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
    console.log(`File "${file.name}" uploaded`);
    setShowUploadModal(false);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold mb-6">System Dashboard</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* System Status */}
        <RetroCard title="System Status">
          <div className="space-y-2">
            {Object.entries(systemHealth.services).map(([name, service]) => (
              <div key={name} className="flex justify-between">
                <span className="text-terminal-cyan">{name.replace('_', ' ').toUpperCase()}</span>
                <StatusIndicator status={service.status} />
              </div>
            ))}
          </div>
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
          {recentOperations.map((operation, index) => (
            <div key={index} className="text-terminal-cyan/80">
              <span className="text-terminal-cyan">&gt;</span> {operation}
            </div>
          ))}
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