import React from 'react';
import { RunAgentPanel } from './RunAgentPanel';

interface RunAgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  agentId?: string;
}

export const RunAgentModal: React.FC<RunAgentModalProps> = ({ 
  isOpen, 
  onClose, 
  agentId 
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-75"
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto mx-4">
        <RunAgentPanel
          agentId={agentId}
          onClose={onClose}
        />
      </div>
    </div>
  );
};