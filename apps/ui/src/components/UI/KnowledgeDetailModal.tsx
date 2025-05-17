import React from 'react';
import { RetroCard } from './RetroCard';
import { RetroButton } from './RetroButton';

interface KnowledgeDetailModalProps {
  item: {
    id: string;
    title: string;
    summary: string;
    tags: string[];
    source: string;
    timestamp: string;
  } | null;
  isOpen: boolean;
  onClose: () => void;
}

export const KnowledgeDetailModal: React.FC<KnowledgeDetailModalProps> = ({ item, isOpen, onClose }) => {
  if (!item || !isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="w-full max-w-2xl max-h-[80vh] overflow-auto">
        <RetroCard title={item.title.toUpperCase()}>
          <div className="space-y-4">
            <div>
              <div className="text-cyan-400 mb-1">SOURCE:</div>
              <div className="text-green-400">{item.source}</div>
            </div>
            
            <div>
              <div className="text-cyan-400 mb-1">TIMESTAMP:</div>
              <div className="text-green-400">{item.timestamp}</div>
            </div>
            
            <div>
              <div className="text-cyan-400 mb-1">TAGS:</div>
              <div className="flex flex-wrap gap-2">
                {item.tags.map(tag => (
                  <span key={tag} className="px-2 py-1 bg-cyan-500 text-black text-sm">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
            
            <div>
              <div className="text-cyan-400 mb-1">SUMMARY:</div>
              <div className="text-green-400 whitespace-pre-wrap">{item.summary}</div>
            </div>
            
            <div className="flex justify-center mt-6">
              <RetroButton variant="primary" onClick={onClose}>
                CLOSE
              </RetroButton>
            </div>
          </div>
        </RetroCard>
      </div>
    </div>
  );
};