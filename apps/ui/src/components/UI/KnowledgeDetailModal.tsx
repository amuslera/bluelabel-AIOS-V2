import React from 'react';
import { RetroCard } from './RetroCard';
import { RetroButton } from './RetroButton';
import type { KnowledgeItem } from '../../api/knowledge';

interface KnowledgeDetailModalProps {
  item: KnowledgeItem | null;
  isOpen: boolean;
  onClose: () => void;
}

export const KnowledgeDetailModal: React.FC<KnowledgeDetailModalProps> = ({
  item,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !item) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 overflow-y-auto">
      <div className="max-w-4xl w-full">
        <RetroCard title={item.title}>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-terminal-cyan/70">TYPE:</span>
                <div className="text-terminal-cyan">{item.type.toUpperCase()}</div>
              </div>
              <div>
                <span className="text-terminal-cyan/70">SOURCE:</span>
                <div className="text-terminal-cyan">{item.source}</div>
              </div>
              <div>
                <span className="text-terminal-cyan/70">PROCESSED BY:</span>
                <div className="text-terminal-cyan">{item.processedBy}</div>
              </div>
              <div>
                <span className="text-terminal-cyan/70">TIMESTAMP:</span>
                <div className="text-terminal-cyan">{item.timestamp}</div>
              </div>
            </div>

            <div>
              <span className="text-terminal-cyan/70">TAGS:</span>
              <div className="flex flex-wrap gap-2 mt-2">
                {item.tags.map(tag => (
                  <span key={tag} className="px-2 py-1 border border-terminal-cyan text-terminal-cyan text-sm">
                    #{tag}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <span className="text-terminal-cyan/70">FULL CONTENT:</span>
              <div className="mt-2 p-4 border border-terminal-cyan/30 max-h-96 overflow-y-auto">
                <p className="text-terminal-cyan whitespace-pre-wrap">{item.summary}</p>
                <div className="mt-4 text-terminal-cyan/60">
                  [Additional content would be loaded here from the API]
                </div>
              </div>
            </div>

            <div className="flex gap-3 justify-end mt-6">
              <RetroButton onClick={onClose} variant="primary">
                CLOSE
              </RetroButton>
            </div>
          </div>
        </RetroCard>
      </div>
    </div>
  );
};