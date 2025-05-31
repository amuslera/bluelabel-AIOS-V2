import React, { useEffect, useState } from 'react';
import { WorkflowStatus, WorkflowStep } from '../../types/roi-workflow';

interface WorkflowProgressProps {
  status: WorkflowStatus;
  className?: string;
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

export function WorkflowProgress({ status, className = '' }: WorkflowProgressProps) {
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
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="text-center">
        <h3 className="text-xl font-terminal text-terminal-cyan mb-2 uppercase">
          Processing Audio Recording
        </h3>
        <p className="text-terminal-cyan/70 text-sm">
          {STEP_MESSAGES[status.status as keyof typeof STEP_MESSAGES] || status.currentStep}
        </p>
      </div>

      {/* Overall Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-terminal-cyan/70">Overall Progress</span>
          <span className="text-terminal-cyan font-terminal">{Math.round(animatedProgress)}%</span>
        </div>
        <div className="w-full bg-terminal-cyan/20 h-3 rounded">
          <div 
            className="bg-terminal-cyan h-3 rounded transition-all duration-500 ease-out"
            style={{ width: `${animatedProgress}%` }}
          />
        </div>
        {status.estimatedTimeRemaining && (
          <div className="text-right text-xs text-terminal-cyan/60">
            {formatTimeRemaining(status.estimatedTimeRemaining)}
          </div>
        )}
      </div>

      {/* Processing Steps */}
      <div className="space-y-4">
        <h4 className="text-lg font-terminal text-terminal-cyan">Processing Steps</h4>
        
        <div className="space-y-3">
          {['uploading', 'transcribing', 'extracting', 'generating'].map((stepId, index) => {
            const stepStatus = getStepStatus(stepId, status.status);
            const isActive = stepId === status.status;
            
            return (
              <div
                key={stepId}
                className={`
                  flex items-center space-x-3 p-3 rounded border transition-all duration-300
                  ${isActive 
                    ? 'border-terminal-cyan bg-terminal-cyan/10' 
                    : stepStatus === 'completed' 
                      ? 'border-terminal-green/50 bg-terminal-green/5' 
                      : stepStatus === 'error'
                        ? 'border-red-500/50 bg-red-500/5'
                        : 'border-terminal-cyan/30'
                  }
                `}
              >
                {/* Step Icon */}
                <div className="text-2xl">
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
                    <h5 className="font-terminal text-terminal-cyan capitalize">
                      {stepId.replace('_', ' ')}
                    </h5>
                    <div className="text-xs text-terminal-cyan/60">
                      {stepStatus === 'completed' && '✓ Complete'}
                      {stepStatus === 'processing' && (
                        <span className="animate-pulse">Processing...</span>
                      )}
                      {stepStatus === 'pending' && 'Pending'}
                      {stepStatus === 'error' && 'Failed'}
                    </div>
                  </div>
                  
                  <p className="text-sm text-terminal-cyan/70 mt-1">
                    {STEP_MESSAGES[stepId as keyof typeof STEP_MESSAGES]}
                  </p>

                  {/* Step Progress Bar */}
                  {isActive && (
                    <div className="mt-2">
                      <div className="w-full bg-terminal-cyan/20 h-1 rounded">
                        <div 
                          className="bg-terminal-cyan h-1 rounded animate-pulse"
                          style={{ width: '60%' }}
                        />
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
        <div className="space-y-3">
          <h4 className="text-lg font-terminal text-terminal-cyan">Detailed Progress</h4>
          
          <div className="space-y-2">
            {status.steps.map((step, index) => (
              <div
                key={step.id}
                className={`
                  flex items-center justify-between p-2 rounded text-sm
                  ${step.status === 'completed' 
                    ? 'bg-terminal-green/10 border border-terminal-green/30' 
                    : step.status === 'processing'
                      ? 'bg-terminal-cyan/10 border border-terminal-cyan/30'
                      : step.status === 'error'
                        ? 'bg-red-500/10 border border-red-500/30'
                        : 'bg-terminal-cyan/5 border border-terminal-cyan/20'
                  }
                `}
              >
                <div className="flex items-center space-x-2">
                  <span className="text-lg">
                    {step.status === 'completed' && '✅'}
                    {step.status === 'processing' && '⚡'}
                    {step.status === 'error' && '❌'}
                    {step.status === 'pending' && '⏳'}
                  </span>
                  <span className="text-terminal-cyan">{step.message}</span>
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
        <div className="p-4 border border-red-500/50 bg-red-500/10 rounded">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-2xl">❌</span>
            <h4 className="font-terminal text-red-400">Processing Failed</h4>
          </div>
          <p className="text-red-300 text-sm">{status.error}</p>
          <p className="text-red-400/70 text-xs mt-2">
            Please try uploading your audio file again or contact support if the issue persists.
          </p>
        </div>
      )}

      {/* Success Message */}
      {status.status === 'completed' && (
        <div className="p-4 border border-terminal-green/50 bg-terminal-green/10 rounded text-center">
          <div className="text-4xl mb-2">🎉</div>
          <h4 className="font-terminal text-terminal-green text-lg mb-2">
            Processing Complete!
          </h4>
          <p className="text-terminal-green/80 text-sm">
            Your audio recording has been successfully processed and the ROI report data is ready.
          </p>
        </div>
      )}

      {/* Processing Animation */}
      {['uploading', 'transcribing', 'extracting', 'generating'].includes(status.status) && (
        <div className="flex justify-center">
          <div className="flex space-x-1">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-2 h-2 bg-terminal-cyan rounded-full animate-pulse"
                style={{ animationDelay: `${i * 0.2}s` }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
} 