import React, { useState } from 'react';
import { RetroCard } from './RetroCard';
import { RetroButton } from './RetroButton';

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File) => void;
}

export const FileUploadModal: React.FC<FileUploadModalProps> = ({
  isOpen,
  onClose,
  onUpload,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      onUpload(selectedFile);
      setSelectedFile(null);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
      <div className="max-w-lg w-full mx-4">
        <RetroCard title="UPLOAD FILE">
          <div 
            className={`border-2 border-dashed p-8 text-center transition-colors ${
              dragOver ? 'border-terminal-green bg-terminal-green/10' : 'border-terminal-cyan'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="text-terminal-cyan mb-4">
              DRAG AND DROP FILE HERE
            </div>
            <div className="text-terminal-cyan/70 mb-4">OR</div>
            <label className="inline-block">
              <input
                type="file"
                className="hidden"
                onChange={handleFileSelect}
                accept=".pdf,.txt,.doc,.docx,.csv,.json"
              />
              <RetroButton>CHOOSE FILE</RetroButton>
            </label>
          </div>

          {selectedFile && (
            <div className="mt-4 p-3 border border-terminal-cyan">
              <div className="text-terminal-cyan">SELECTED FILE:</div>
              <div className="text-terminal-green">{selectedFile.name}</div>
              <div className="text-terminal-cyan/70 text-sm">
                Size: {(selectedFile.size / 1024).toFixed(2)} KB
              </div>
            </div>
          )}

          <div className="flex gap-3 mt-6">
            <RetroButton 
              onClick={handleUpload} 
              variant="success"
              disabled={!selectedFile}
            >
              UPLOAD
            </RetroButton>
            <RetroButton onClick={onClose} variant="error">
              CANCEL
            </RetroButton>
          </div>
        </RetroCard>
      </div>
    </div>
  );
};