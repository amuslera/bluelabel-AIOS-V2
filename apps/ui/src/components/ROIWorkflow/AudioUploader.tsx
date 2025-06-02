import React, { useState, useRef, useCallback } from 'react';
import { AudioFile } from '../../types/roi-workflow';
import { roiWorkflowAPI } from '../../api/roi-workflow';
import { RecordingGuide } from './RecordingGuide';

interface AudioUploaderProps {
  onFileSelect: (audioFile: AudioFile) => void;
  onUploadStart: () => void;
  onUploadProgress: (progress: number) => void;
  onUploadComplete: (workflowId: string) => void;
  onUploadError: (error: string) => void;
  onCancel?: () => void;
  disabled?: boolean;
}

export function AudioUploader({
  onFileSelect,
  onUploadStart,
  onUploadProgress,
  onUploadComplete,
  onUploadError,
  onCancel,
  disabled = false
}: AudioUploaderProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<AudioFile | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [showRecordingTemplate, setShowRecordingTemplate] = useState(false);
  const [showSuccessAnimation, setShowSuccessAnimation] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordingChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);

  const createAudioFile = useCallback(async (file: File): Promise<AudioFile> => {
    return new Promise((resolve) => {
      const url = URL.createObjectURL(file);
      const audio = new Audio(url);
      
      audio.addEventListener('loadedmetadata', () => {
        resolve({
          file,
          url,
          duration: audio.duration,
          size: file.size,
          format: file.type,
          name: file.name
        });
      });

      audio.addEventListener('error', () => {
        resolve({
          file,
          url,
          size: file.size,
          format: file.type,
          name: file.name
        });
      });
    });
  }, []);

  const handleFileSelection = useCallback(async (file: File) => {
    if (disabled || isUploading) return;

    // Validate file
    const validation = await roiWorkflowAPI.validateAudioFile(file);
    if (!validation.valid) {
      onUploadError(validation.error || 'Invalid file');
      return;
    }

    // Create audio file object
    const audioFile = await createAudioFile(file);
    setSelectedFile(audioFile);
    onFileSelect(audioFile);
  }, [disabled, isUploading, createAudioFile, onFileSelect, onUploadError]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelection(files[0]);
    }
  }, [handleFileSelection]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled && !isUploading) {
      setIsDragOver(true);
    }
  }, [disabled, isUploading]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelection(files[0]);
    }
  }, [handleFileSelection]);

  const handleUpload = useCallback(async () => {
    if (!selectedFile || isUploading) return;

    setIsUploading(true);
    setUploadProgress(0);
    onUploadStart();

    try {
      const response = await roiWorkflowAPI.uploadAudio(
        selectedFile.file,
        (progress) => {
          setUploadProgress(progress);
          onUploadProgress(progress);
        }
      );

      // Show success animation
      setShowSuccessAnimation(true);
      setTimeout(() => setShowSuccessAnimation(false), 2000);
      
      onUploadComplete(response.workflowId);
    } catch (error: any) {
      onUploadError(error.message);
    } finally {
      setIsUploading(false);
    }
  }, [selectedFile, isUploading, onUploadStart, onUploadProgress, onUploadComplete, onUploadError]);

  const removeFile = useCallback(() => {
    if (selectedFile) {
      URL.revokeObjectURL(selectedFile.url);
    }
    setSelectedFile(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [selectedFile]);

  const formatTime = useCallback((seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Create MediaRecorder with appropriate mime type
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') 
        ? 'audio/webm' 
        : 'audio/ogg';
      
      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordingChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const recordingBlob = new Blob(recordingChunksRef.current, { type: mimeType });
        const recordingFile = new File([recordingBlob], `recording_${Date.now()}.webm`, { type: mimeType });
        
        // Clean up
        stream.getTracks().forEach(track => track.stop());
        recordingChunksRef.current = [];
        
        // Create audio file object and select it
        const audioFile = await createAudioFile(recordingFile);
        setSelectedFile(audioFile);
        onFileSelect(audioFile);
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      
      setIsRecording(true);
      setRecordingTime(0);
      setShowRecordingTemplate(true);
      
      // Start timer
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (error: any) {
      console.error('Error starting recording:', error);
      onUploadError('Failed to start recording. Please check microphone permissions.');
    }
  }, [createAudioFile, onFileSelect, onUploadError]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
      
      setIsRecording(false);
      setShowRecordingTemplate(false);
    }
  }, []);

  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
      
      // Clean up recording chunks
      recordingChunksRef.current = [];
      
      setIsRecording(false);
      setShowRecordingTemplate(false);
      setRecordingTime(0);
    }
  }, []);

  return (
    <div className="w-full space-y-6">
      {/* File Drop Zone */}
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 ease-in-out
          ${isDragOver 
            ? 'border-terminal-cyan bg-terminal-cyan/10 scale-105 shadow-lg shadow-terminal-cyan/20' 
            : 'border-terminal-cyan/50 hover:border-terminal-cyan hover:shadow-md hover:shadow-terminal-cyan/10'
          }
          ${disabled || isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:bg-terminal-cyan/5'}
        `}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => !disabled && !isUploading && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*"
          onChange={handleFileInputChange}
          className="hidden"
          disabled={disabled || isUploading}
        />

        <div className="space-y-4">
          <div className="text-terminal-cyan text-4xl transition-transform duration-200 hover:scale-110">🎤</div>
          
          <div>
            <h3 className="text-lg font-terminal text-terminal-cyan mb-2">
              Upload Audio Recording
            </h3>
            <p className="text-terminal-cyan/70 text-sm">
              Drag and drop your audio file here, or click to browse
            </p>
            <p className="text-terminal-cyan/50 text-xs mt-2">
              Supported formats: MP3, M4A, WAV, WEBM (max 100MB)
            </p>
          </div>

          {isDragOver && (
            <div className="text-terminal-cyan font-terminal animate-bounce">
              Drop your audio file here!
            </div>
          )}
          
          {showSuccessAnimation && (
            <div className="text-green-400 font-terminal animate-pulse text-lg">
              ✅ File uploaded successfully!
            </div>
          )}
        </div>
      </div>

      {/* Selected File Info */}
      {selectedFile && (
        <div className="border border-terminal-cyan/30 rounded-lg p-6 bg-terminal-bg/50 shadow-md transition-all duration-200 hover:shadow-lg hover:shadow-terminal-cyan/10">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-terminal-cyan font-terminal">Selected File</h4>
            <button
              onClick={removeFile}
              disabled={isUploading}
              className="text-terminal-cyan/70 hover:text-terminal-cyan text-sm disabled:opacity-50 transition-all duration-200 hover:scale-105 px-2 py-1 rounded"
            >
              [REMOVE]
            </button>
          </div>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-1">
              <span className="text-terminal-cyan/70">Name:</span>
              <span className="text-terminal-cyan font-medium">{selectedFile.name}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-terminal-cyan/70">Size:</span>
              <span className="text-terminal-cyan">
                {roiWorkflowAPI.formatFileSize(selectedFile.size)}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-terminal-cyan/70">Format:</span>
              <span className="text-terminal-cyan">{selectedFile.format}</span>
            </div>
            {selectedFile.duration && (
              <div className="flex justify-between py-1">
                <span className="text-terminal-cyan/70">Duration:</span>
                <span className="text-terminal-cyan">
                  {roiWorkflowAPI.formatDuration(selectedFile.duration)}
                </span>
              </div>
            )}
          </div>

          {/* Audio Preview */}
          <div className="mt-4">
            <audio
              ref={audioRef}
              controls
              className="w-full rounded-lg"
              src={selectedFile.url}
            />
          </div>

          {/* Upload Progress */}
          {isUploading && (
            <div className="mt-6">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-terminal-cyan/70">Processing...</span>
                <span className="text-terminal-cyan font-terminal">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-terminal-cyan/20 h-3 rounded-lg overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-terminal-cyan to-terminal-green h-3 rounded-lg transition-all duration-300 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              {onCancel && (
                <button
                  onClick={() => {
                    setIsUploading(false);
                    setUploadProgress(0);
                    removeFile();
                    onCancel();
                  }}
                  className="w-full mt-4 px-6 py-3 border border-red-400 text-red-400 font-terminal uppercase hover:bg-red-400/10 transition-all duration-200 rounded-lg hover:scale-105"
                >
                  Cancel Processing
                </button>
              )}
            </div>
          )}

          {/* Upload Button */}
          {!isUploading && (
            <div className="flex gap-4 mt-6">
              {onCancel && (
                <button
                  onClick={() => {
                    removeFile();
                    onCancel();
                  }}
                  className="flex-1 px-6 py-3 border border-terminal-cyan text-terminal-cyan font-terminal uppercase hover:bg-terminal-cyan/10 transition-all duration-200 rounded-lg hover:scale-105 hover:shadow-md"
                >
                  Cancel
                </button>
              )}
              <button
                onClick={handleUpload}
                disabled={disabled}
                className="flex-1 px-6 py-3 bg-terminal-cyan text-black font-terminal uppercase hover:bg-terminal-cyan/80 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg hover:scale-105 hover:shadow-lg disabled:hover:scale-100"
              >
                Process Audio Recording
              </button>
            </div>
          )}
        </div>
      )}

      {/* Recording Section */}
      {!selectedFile && (
        <div className="border border-terminal-cyan/30 rounded-lg p-6 bg-terminal-bg/50 shadow-md transition-all duration-200 hover:shadow-lg hover:shadow-terminal-cyan/10">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-terminal-cyan font-terminal">Record Audio</h4>
            {isRecording && (
              <span className="text-terminal-cyan text-sm font-terminal animate-pulse">
                {formatTime(recordingTime)}
              </span>
            )}
          </div>

          {!isRecording ? (
            <button
              onClick={startRecording}
              disabled={disabled || isUploading}
              className="w-full px-6 py-4 bg-terminal-cyan/20 border border-terminal-cyan text-terminal-cyan font-terminal uppercase hover:bg-terminal-cyan/30 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-4 rounded-lg hover:scale-105 hover:shadow-lg disabled:hover:scale-100"
            >
              <span className="text-2xl transition-transform duration-200 hover:scale-110">🎙️</span>
              <span>Start Recording</span>
            </button>
          ) : (
            <div className="space-y-6">
              {/* Recording Animation */}
              <div className="flex items-center justify-center py-6">
                <div className="relative">
                  <div className="w-20 h-20 rounded-full bg-red-500 animate-pulse flex items-center justify-center shadow-lg">
                    <span className="text-3xl">🎙️</span>
                  </div>
                  <div className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-75"></div>
                  <div className="absolute inset-0 rounded-full bg-red-400 animate-ping opacity-50 animation-delay-75"></div>
                </div>
              </div>

              {/* Voice Template */}
              {showRecordingTemplate && (
                <RecordingGuide language="en" />
              )}

              <div className="flex gap-4">
                <button
                  onClick={cancelRecording}
                  className="flex-1 px-6 py-4 bg-gray-500 text-white font-terminal uppercase hover:bg-gray-600 transition-all duration-200 flex items-center justify-center gap-3 rounded-lg hover:scale-105 hover:shadow-lg"
                >
                  <span>❌</span>
                  <span>Cancel</span>
                </button>
                <button
                  onClick={stopRecording}
                  className="flex-1 px-6 py-4 bg-red-500 text-white font-terminal uppercase hover:bg-red-600 transition-all duration-200 flex items-center justify-center gap-3 rounded-lg hover:scale-105 hover:shadow-lg"
                >
                  <span>⏹️</span>
                  <span>Finish</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Quick Tips */}
      <div className="text-xs text-terminal-cyan/60 space-y-2 p-4 bg-terminal-cyan/5 rounded-lg border border-terminal-cyan/20">
        <p className="flex items-center gap-2"><span>💡</span><strong>Quick Tips:</strong></p>
        <div className="ml-6 space-y-1">
          <p>• Speak clearly and naturally</p>
          <p>• Both English and Spanish are supported</p>
          <p>• Recording will be transcribed and structured automatically</p>
        </div>
      </div>
    </div>
  );
} 