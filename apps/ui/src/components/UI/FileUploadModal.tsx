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
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="w-full max-w-md">
        <RetroCard title="UPLOAD FILE">
          <div
            className={`border-2 border-dashed ${
              dragOver ? 'border-green-400' : 'border-cyan-400'
            } p-8 text-center transition-colors`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
          >
            <input
              type="file"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="text-cyan-400 mb-4">
                {selectedFile ? (
                  <>
                    <div className="text-green-400">Selected:</div>
                    <div>{selectedFile.name}</div>
                    <div className="text-sm mt-2">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </div>
                  </>
                ) : (
                  <>DROP FILE HERE OR CLICK TO SELECT</>
                )}
              </div>
            </label>
          </div>
          <div className="flex justify-between mt-4">
            <RetroButton variant="error" onClick={onClose}>
              CANCEL
            </RetroButton>
            <RetroButton
              variant="primary"
              onClick={handleUpload}
              disabled={!selectedFile}
            >
              UPLOAD
            </RetroButton>
          </div>
        </RetroCard>
      </div>
    </div>
  );
};