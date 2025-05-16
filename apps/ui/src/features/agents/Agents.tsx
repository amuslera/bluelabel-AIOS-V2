import React, { useState, useEffect } from 'react';
import { RetroCard } from '../../components/UI/RetroCard';
import { RetroButton } from '../../components/UI/RetroButton';
import { RetroLoader } from '../../components/UI/RetroLoader';
import { agentsAPI } from '../../api/agents';
import type { Agent } from '../../api/agents';

export const Agents: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const data = await agentsAPI.getAgents();
        setAgents(data);
      } catch (err) {
        // Fallback to mock data
        setAgents([
          { id: '1', name: 'ContentMind', type: 'content', status: 'active', lastRun: '5 min ago' },
          { id: '2', name: 'ContextMind', type: 'context', status: 'inactive', lastRun: '1 hour ago' },
          { id: '3', name: 'WebFetcher', type: 'web', status: 'active', lastRun: '30 min ago' },
        ]);
      } finally {
        setLoading(false);
      }
    };
    fetchAgents();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RetroLoader text="Loading agents..." size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold mb-6 text-terminal-cyan">AGENT CONTROL</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {agents.map(agent => (
          <RetroCard key={agent.id} title={agent.name.toUpperCase()}>
            <div className="space-y-3">
              <div>
                <span className="text-terminal-cyan/70">TYPE:</span>
                <div className="text-terminal-cyan">{agent.type.toUpperCase()}</div>
              </div>
              <div>
                <span className="text-terminal-cyan/70">STATUS:</span>
                <div className={agent.status === 'active' ? 'text-terminal-green' : 'text-terminal-amber'}>
                  [{agent.status.toUpperCase()}]
                </div>
              </div>
              <div>
                <span className="text-terminal-cyan/70">LAST RUN:</span>
                <div className="text-terminal-cyan">{agent.lastRun || 'NEVER'}</div>
              </div>
              <div className="pt-3">
                <RetroButton 
                  onClick={() => setSelectedAgent(agent)} 
                  variant={agent.status === 'active' ? 'primary' : 'warning'}
                >
                  {agent.status === 'active' ? 'RUN AGENT' : 'ACTIVATE'}
                </RetroButton>
              </div>
            </div>
          </RetroCard>
        ))}
      </div>

      {selectedAgent && (
        <RetroCard title={`EXECUTE ${selectedAgent.name.toUpperCase()}`}>
          <div className="text-terminal-cyan mb-4">
            Agent execution interface would appear here
          </div>
          <RetroButton onClick={() => setSelectedAgent(null)} variant="error">
            CANCEL
          </RetroButton>
        </RetroCard>
      )}
    </div>
  );
};