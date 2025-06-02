import React, { useEffect, useState } from 'react';
import { WorkflowStatus } from '../../types/roi-workflow';

interface WorkflowProgressProps {
  status: WorkflowStatus;
  className?: string;
  onCancel?: () => void;
}

const STEP_ICONS = {
  uploading: '📤',
  transcribing: '🎧',
  extracting: '🔍',
  generating: '📊',
  completed: '✅',
  error: '❌'
};

const STEP_MESSAGES = {
  uploading: 'Uploading audio file...',
  transcribing: 'Transcribing audio (Spanish/English detection)...',
  extracting: 'Extracting meeting metadata...',
  generating: 'Generating ROI report...',
  completed: 'Processing complete!',
  error: 'Processing failed'
};

export function WorkflowProgress({ status, className = '', onCancel }: WorkflowProgressProps) {
  const [animatedProgress, setAnimatedProgress] = useState(0);

  useEffect(() => {
    // Animate progress changes
    const timer = setTimeout(() => {
      setAnimatedProgress(status.progress);
    }, 100);

    return () => clearTimeout(timer);
  }, [status.progress]);

  const formatTimeRemaining = (seconds?: number): string => {
    if (!seconds) return '';
    
    if (seconds < 60) {
      return `${Math.round(seconds)}s remaining`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}m ${remainingSeconds}s remaining`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m remaining`;
    }
  };

  const getStepStatus = (stepId: string, currentStatus: string): 'completed' | 'processing' | 'pending' | 'error' => {
    if (status.status === 'error') return 'error';
    
    const stepOrder = ['uploading', 'transcribing', 'extracting', 'generating'];
    const currentIndex = stepOrder.indexOf(currentStatus);
    const stepIndex = stepOrder.indexOf(stepId);
    
    if (stepIndex < currentIndex || currentStatus === 'completed') return 'completed';
    if (stepIndex === currentIndex) return 'processing';
    return 'pending';
  };

  return (
    <div className={`space-y-8 ${className}`}>
      {/* Header */}
      <div className="text-center p-6 bg-terminal-cyan/5 rounded-lg border border-terminal-cyan/20 shadow-md">
        <h3 className="text-xl font-terminal text-terminal-cyan mb-3 uppercase tracking-wider">
          Processing Audio Recording
        </h3>
        <p className="text-terminal-cyan/70 text-sm">
          {STEP_MESSAGES[status.status as keyof typeof STEP_MESSAGES] || status.currentStep}
        </p>
      </div>

      {/* Overall Progress Bar */}
      <div className="space-y-4 p-6 bg-terminal-bg/50 rounded-lg border border-terminal-cyan/30 shadow-md">
        <div className="flex justify-between text-sm">
          <span className="text-terminal-cyan/70 font-medium">Overall Progress</span>
          <span className="text-terminal-cyan font-terminal text-lg">{Math.round(animatedProgress)}%</span>
        </div>
        <div className="w-full bg-terminal-cyan/20 h-4 rounded-lg overflow-hidden shadow-inner">
          <div 
            className="bg-gradient-to-r from-terminal-cyan to-terminal-green h-4 rounded-lg transition-all duration-500 ease-out shadow-sm"
            style={{ width: `${animatedProgress}%` }}
          />
        </div>
        {status.estimatedTimeRemaining && (
          <div className="text-right text-xs text-terminal-cyan/60 font-medium">
            {formatTimeRemaining(status.estimatedTimeRemaining)}
          </div>
        )}
      </div>

      {/* Processing Steps */}
      <div className="space-y-6">
        <h4 className="text-lg font-terminal text-terminal-cyan tracking-wide">Processing Steps</h4>
        
        <div className="space-y-4">
          {['uploading', 'transcribing', 'extracting', 'generating'].map((stepId, index) => {
            const stepStatus = getStepStatus(stepId, status.status);
            const isActive = stepId === status.status;
            
            return (
              <div
                key={stepId}
                className={`
                  flex items-center space-x-4 p-4 rounded-lg border transition-all duration-300 hover:shadow-lg group
                  ${isActive 
                    ? 'border-terminal-cyan bg-terminal-cyan/10 shadow-md shadow-terminal-cyan/20 scale-105' 
                    : stepStatus === 'completed' 
                      ? 'border-terminal-green/50 bg-terminal-green/5 shadow-md' 
                      : stepStatus === 'error'
                        ? 'border-red-500/50 bg-red-500/5 shadow-md'
                        : 'border-terminal-cyan/30 hover:border-terminal-cyan/50 hover:bg-terminal-cyan/5'
                  }
                `}
              >
                {/* Step Icon */}
                <div className={`text-3xl transition-transform duration-300 ${isActive ? 'animate-pulse scale-110' : 'group-hover:scale-110'}`}>
                  {stepStatus === 'error' 
                    ? STEP_ICONS.error 
                    : stepStatus === 'completed' 
                      ? STEP_ICONS.completed 
                      : STEP_ICONS[stepId as keyof typeof STEP_ICONS]
                  }
                </div>

                {/* Step Content */}
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h5 className="font-terminal text-terminal-cyan capitalize text-lg">
                      {stepId.replace('_', ' ')}
                    </h5>
                    <div className="text-xs text-terminal-cyan/60 font-medium">
                      {stepStatus === 'completed' && (
                        <span className="text-terminal-green animate-bounce">✓ Complete</span>
                      )}
                      {stepStatus === 'processing' && (
                        <span className="animate-pulse text-terminal-cyan">Processing...</span>
                      )}
                      {stepStatus === 'pending' && (
                        <span className="text-terminal-cyan/40">Pending</span>
                      )}
                      {stepStatus === 'error' && (
                        <span className="text-red-400">Failed</span>
                      )}
                    </div>
                  </div>
                  
                  <p className="text-sm text-terminal-cyan/70 mt-2">
                    {STEP_MESSAGES[stepId as keyof typeof STEP_MESSAGES]}
                  </p>

                  {/* Step Progress Bar */}
                  {isActive && (
                    <div className="mt-3">
                      <div className="w-full bg-terminal-cyan/20 h-2 rounded-lg overflow-hidden">
                        <div className="bg-terminal-cyan h-2 rounded-lg animate-pulse shadow-sm" style={{ width: '60%' }} />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Detailed Steps (if available) */}
      {status.steps && status.steps.length > 0 && (
        <div className="space-y-4 p-6 bg-terminal-bg/30 rounded-lg border border-terminal-cyan/20 shadow-md">
          <h4 className="text-lg font-terminal text-terminal-cyan tracking-wide">Detailed Progress</h4>
          
          <div className="space-y-3">
            {status.steps.map((step, index) => (
              <div
                key={step.id}
                className={`
                  flex items-center justify-between p-3 rounded-lg text-sm transition-all duration-200 hover:scale-105
                  ${step.status === 'completed' 
                    ? 'bg-terminal-green/10 border border-terminal-green/30 shadow-md' 
                    : step.status === 'processing'
                      ? 'bg-terminal-cyan/10 border border-terminal-cyan/30 shadow-md'
                      : step.status === 'error'
                        ? 'bg-red-500/10 border border-red-500/30 shadow-md'
                        : 'bg-terminal-cyan/5 border border-terminal-cyan/20'
                  }
                `}
              >
                <div className="flex items-center space-x-3">
                  <span className="text-lg">
                    {step.status === 'completed' && '✅'}
                    {step.status === 'processing' && '⚡'}
                    {step.status === 'error' && '❌'}
                    {step.status === 'pending' && '⏳'}
                  </span>
                  <span className="text-terminal-cyan font-medium">{step.message}</span>
                </div>
                
                <div className="text-terminal-cyan/60 text-xs">
                  {step.progress && `${step.progress}%`}
                  {step.estimatedTime && ` • ${formatTimeRemaining(step.estimatedTime)}`}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Display */}
      {status.status === 'error' && status.error && (
        <div className="p-6 border border-red-500/50 bg-red-500/10 rounded-lg shadow-lg">
          <div className="flex items-center space-x-3 mb-3">
            <span className="text-3xl animate-bounce">❌</span>
            <h4 className="font-terminal text-red-400 text-lg">Processing Failed</h4>
          </div>
          <p className="text-red-300 text-sm mb-3">{status.error}</p>
          <p className="text-red-400/70 text-xs">
            Please try uploading your audio file again or contact support if the issue persists.
          </p>
        </div>
      )}

      {/* Success Message */}
      {status.status === 'completed' && (
        <div className="p-6 border border-terminal-green/50 bg-terminal-green/10 rounded-lg text-center shadow-lg">
          <div className="text-5xl mb-4 animate-bounce">🎉</div>
          <h4 className="font-terminal text-terminal-green text-xl mb-3 tracking-wide">
            Processing Complete!
          </h4>
          <p className="text-terminal-green/80 text-sm">
            Your audio recording has been successfully processed and the ROI report data is ready.
          </p>
        </div>
      )}

      {/* Processing Animation */}
      {['uploading', 'transcribing', 'extracting', 'generating'].includes(status.status) && (
        <div className="flex justify-center py-4">
          <div className="flex space-x-2">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-3 h-3 bg-terminal-cyan rounded-full animate-pulse shadow-md"
                style={{ animationDelay: `${i * 0.2}s` }}
              />
            ))}
          </div>
        </div>
      )}
      
      {/* Cancel Button */}
      {onCancel && ['uploading', 'transcribing', 'extracting', 'generating'].includes(status.status) && (
        <div className="flex justify-center pt-6">
          <button
            onClick={onCancel}
            className="px-8 py-3 border border-red-400 text-red-400 font-terminal uppercase hover:bg-red-400/10 transition-all duration-200 rounded-lg hover:scale-105 hover:shadow-lg"
          >
            Cancel Processing
          </button>
        </div>
      )}
    </div>
  );
} 