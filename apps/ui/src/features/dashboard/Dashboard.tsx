import React, { useEffect, useState } from 'react';
import { RetroButton } from '../../components/UI/RetroButton';
import { RetroCard } from '../../components/UI/RetroCard';
import { RetroLoader } from '../../components/UI/RetroLoader';

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
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setSystemStatus({
        status: 'online',
        components: {
          content_mind: { status: 'ok', lastCheck: '2 min ago' },
          email_gateway: { status: 'ok', lastCheck: '5 min ago' },
          model_router: { status: 'ok', lastCheck: '1 min ago' },
          redis: { status: 'ok', lastCheck: '30 sec ago' },
        },
      });
      
      setActivities([
        { time: '10:42', type: 'Email processed', from: 'john@example.com' },
        { time: '10:38', type: 'WhatsApp received', from: '+1234567890' },
        { time: '10:35', type: 'Agent run', from: 'ContentMind' },
      ]);
      
      setLoading(false);
    }, 1000);
  }, []);

  const StatusIndicator: React.FC<{ status: string }> = ({ status }) => {
    const colors = {
      ok: 'text-terminal-green',
      error: 'text-error-pink',
      warning: 'text-terminal-amber',
      online: 'text-terminal-green',
      offline: 'text-error-pink',
    };
    
    return (
      <span className={`font-bold ${colors[status as keyof typeof colors] || 'text-terminal-cyan'} retro-glow`}>
        [{status.toUpperCase()}]
      </span>
    );
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
      <h2 className="text-2xl font-bold mb-6 retro-glow">System Dashboard</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* System Status */}
        <RetroCard title="System Status">
          {systemStatus && systemStatus.components ? (
            <div className="space-y-2">
              {Object.entries(systemStatus.components).map(([name, component]) => (
                <div key={name} className="flex justify-between">
                  <span className="text-terminal-cyan">{name.replace('_', ' ').toUpperCase()}</span>
                  <StatusIndicator status={component.status} />
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
            {activities.map((activity, index) => (
              <div key={index} className="text-terminal-cyan">
                <span className="text-terminal-cyan/70">{activity.time}</span> - {activity.type}
                <div className="text-sm text-terminal-cyan/50 ml-4">→ {activity.from}</div>
              </div>
            ))}
          </div>
        </RetroCard>
      </div>

      {/* Quick Actions */}
      <RetroCard title="Quick Actions">
        <div className="flex flex-wrap gap-4">
          <RetroButton onClick={() => console.log('Run Agent')}>
            RUN AGENT
          </RetroButton>
          <RetroButton onClick={() => console.log('Upload File')} variant="success">
            UPLOAD FILE
          </RetroButton>
          <RetroButton onClick={() => console.log('View Logs')} variant="warning">
            VIEW LOGS
          </RetroButton>
          <RetroButton onClick={() => window.location.href = '/terminal'} variant="primary">
            OPEN TERMINAL
          </RetroButton>
        </div>
      </RetroCard>

      {/* Terminal Preview */}
      <RetroCard>
        <div className="font-mono">
          <div className="text-terminal-cyan mb-2 retro-glow">&gt; status</div>
          <div className="text-terminal-cyan">SYSTEM STATUS: ONLINE</div>
          <div className="text-terminal-cyan">ContentMind    [OK]</div>
          <div className="text-terminal-cyan">Email Gateway  [OK]</div>
          <div className="text-terminal-cyan">Model Router   [OK]</div>
          <div className="text-terminal-cyan">Redis          [OK]</div>
          <div className="text-terminal-cyan mt-4 retro-glow">&gt; <span className="cursor">_</span></div>
        </div>
      </RetroCard>
    </div>
  );
};