import React, { useState, useEffect, useRef } from 'react';
import { AudioUploader } from './AudioUploader';
import { WorkflowProgress } from './WorkflowProgress';
import { ResultsTable } from './ResultsTable';
import { ExportOptions } from './ExportOptions';
import { 
  AudioFile, 
  WorkflowStatus, 
  WorkflowResult, 
  ROIReportData 
} from '../../types/roi-workflow';
import { roiWorkflowAPI } from '../../api/roi-workflow';

type WorkflowPhase = 'upload' | 'processing' | 'results' | 'error';

interface ROIWorkflowContainerProps {
  className?: string;
}

export function ROIWorkflowContainer({ className = '' }: ROIWorkflowContainerProps) {
  const [phase, setPhase] = useState<WorkflowPhase>('upload');
  const [selectedFile, setSelectedFile] = useState<AudioFile | null>(null);
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [results, setResults] = useState<ROIReportData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<string>('');
  const [transcriptEnglish, setTranscriptEnglish] = useState<string>('');
  const [language, setLanguage] = useState<'en' | 'es' | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);

  // Sample data for demo purposes
  const sampleData: ROIReportData[] = [
    {
      id: '1',
      name: 'John Smith',
      company: 'TechCorp Solutions',
      position: 'Chief Technology Officer',
      discussion: 'Discussed our AI automation platform integration, potential for 50% workflow efficiency improvement, budget considerations for Q1 implementation.',
      contactType: 'prospective',
      priorityLevel: 'high',
      actionItems: ['Send detailed proposal by Friday', 'Schedule technical demo with engineering team', 'Prepare cost analysis for 100-user deployment']
    },
    {
      id: '2', 
      name: 'Maria Rodriguez',
      company: 'Global Consulting Inc',
      position: 'Operations Director',
      discussion: 'Review of current contract performance, discussed expanding services to European markets, very satisfied with current ROI.',
      contactType: 'existing',
      priorityLevel: 'medium',
      actionItems: ['Prepare market expansion proposal', 'Coordinate with European team leads']
    }
  ];

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Monitor workflow status changes
  useEffect(() => {
    if (workflowStatus?.status === 'completed') {
      handleWorkflowComplete();
    } else if (workflowStatus?.status === 'error' || workflowStatus?.status === 'failed') {
      setPhase('error');
      const errorMessage = workflowStatus.error || workflowStatus.error_message || 'Processing failed';
      console.error('Workflow status error:', errorMessage);
      setError(errorMessage);
    }
  }, [workflowStatus]);

  const handleFileSelect = (audioFile: AudioFile) => {
    setSelectedFile(audioFile);
    setError(null);
  };

  const handleUploadStart = () => {
    setPhase('processing');
    setError(null);
  };

  const handleUploadProgress = (progress: number) => {
    // Update upload progress if needed
  };

  const handleUploadComplete = (workflowIdValue: string) => {
    setWorkflowId(workflowIdValue);
    
    // Initialize workflow status
    setWorkflowStatus({
      id: workflowIdValue,
      status: 'uploaded',
      steps: [],
      progress: 10,
      currentStep: 'Starting processing...'
    });

    // Start polling for real updates
    startRealTimePolling(workflowIdValue);
  };

  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage);
    setPhase('error');
  };

  const startRealTimePolling = (workflowIdValue: string) => {
    try {
      roiWorkflowAPI.pollWorkflowStatus(
        workflowIdValue,
        (status: any) => {
          console.log('Workflow status update:', status);
          // Map backend status to frontend display
          const displayStatus = mapStatusToDisplay(status);
          setWorkflowStatus(displayStatus);
          
          // Check for errors in the status update
          if (status.error || status.error_message) {
            console.error('Error in status update:', status.error || status.error_message);
          }
        },
        (result: WorkflowResult) => {
          // Workflow completed successfully
          handleRealWorkflowComplete(result);
        }
      );
    } catch (error) {
      console.error('Failed to start polling:', error);
      setError('Failed to monitor workflow progress');
      setPhase('error');
    }
  };

  const mapStatusToDisplay = (backendStatus: any): WorkflowStatus => {
    const statusMap: { [key: string]: { progress: number; message: string } } = {
      'uploaded': { progress: 15, message: 'Processing started...' },
      'transcribing': { progress: 40, message: 'Transcribing audio (Whisper AI)...' },
      'extracting': { progress: 70, message: 'Extracting structured data (GPT-4)...' },
      'completed': { progress: 100, message: 'Processing complete!' },
      'failed': { progress: 0, message: 'Processing failed' },
      'error': { progress: 0, message: 'Processing error' }
    };

    const mapped = statusMap[backendStatus.status] || { progress: 20, message: 'Processing...' };
    
    return {
      id: backendStatus.id,
      status: backendStatus.status,
      steps: [],
      progress: mapped.progress,
      currentStep: mapped.message,
      error: backendStatus.error_message
    };
  };

  const handleRealWorkflowComplete = async (result: any) => {
    try {
      console.log('Workflow result received:', result);
      console.log('Result keys:', Object.keys(result));
      console.log('Result type:', typeof result);
      
      // Check if workflow failed
      if (result.status === 'failed' || result.status === 'error') {
        const errorMessage = result.error || result.error_message || 'Workflow failed';
        console.error('Workflow failed with error:', errorMessage);
        throw new Error(errorMessage);
      }

      // Extract data from the result - handle different backend response formats
      const transcription = result.transcript || result.transcription || '';
      const transcriptionEnglish = result.transcription_english || result.transcript_english || '';
      const detectedLanguage = result.language || result.language_detected || 'en';
      
      console.log('Transcription found:', transcription);
      console.log('English transcription found:', transcriptionEnglish);
      console.log('Language detected:', detectedLanguage);
      
      // Try to get extracted data from various possible locations
      let extractedData = result.data || result.extracted_data || result.results || null;
      
      // If data is nested under a results property
      if (!extractedData && result.results && typeof result.results === 'object') {
        extractedData = result.results.data || result.results.extracted_data || null;
      }
      
      console.log('Extracted data:', extractedData);
      console.log('Extracted data type:', typeof extractedData);
      console.log('Extracted data is array?', Array.isArray(extractedData));

      // Convert backend data to frontend format
      const formattedResults: ROIReportData[] = [];
      
      // Handle array of data (multiple contacts)
      if (Array.isArray(extractedData)) {
        console.log('Processing array of', extractedData.length, 'items');
        extractedData.forEach((item, index) => {
          console.log(`Item ${index}:`, item);
          formattedResults.push({
            id: (index + 1).toString(),
            name: item.name || 'Not specified',
            company: item.company || 'Not specified',
            position: item.position || 'Not specified',
            discussion: item.discussion || 'Not specified',
            contactType: (item.contact_type || item.contactType || 'prospective').toLowerCase() as 'prospective' | 'existing',
            priorityLevel: (item.priority || item.priorityLevel || item.priority_level || 'medium').toLowerCase() as 'high' | 'medium' | 'low',
            actionItems: item.action_items || item.actionItems || []
          });
        });
      } 
      // Handle single object data
      else if (extractedData && typeof extractedData === 'object' && !Array.isArray(extractedData)) {
        console.log('Processing single object:', extractedData);
        
        // Check if it's wrapped in a list with one item
        if (extractedData.length === 1 && Array.isArray(extractedData)) {
          extractedData = extractedData[0];
        }
        
        formattedResults.push({
          id: '1',
          name: extractedData.name || 'Not specified',
          company: extractedData.company || 'Not specified',
          position: extractedData.position || 'Not specified',
          discussion: extractedData.discussion || 'Not specified',
          contactType: (extractedData.contact_type || extractedData.contactType || 'prospective').toLowerCase() as 'prospective' | 'existing',
          priorityLevel: (extractedData.priority || extractedData.priorityLevel || extractedData.priority_level || 'medium').toLowerCase() as 'high' | 'medium' | 'low',
          actionItems: extractedData.action_items || extractedData.actionItems || []
        });
      } else {
        console.warn('No extracted data found in result');
        console.log('Full result object for debugging:', JSON.stringify(result, null, 2));
      }

      console.log('Formatted results:', formattedResults);
      console.log('Number of results:', formattedResults.length);
      
      setResults(formattedResults);
      setTranscript(transcription || 'No transcription available');
      setTranscriptEnglish(transcriptionEnglish);
      setLanguage(detectedLanguage === 'spanish' || detectedLanguage === 'es' ? 'es' : 'en');
      setPhase('results');
    } catch (error: any) {
      console.error('Failed to process workflow results:', error);
      console.error('Error stack:', error.stack);
      setError('Failed to process workflow results: ' + error.message);
      setPhase('error');
    }
  };

  // Keep the old handler for backward compatibility but make it use real data
  const handleWorkflowComplete = async () => {
    if (!workflowId) return;

    try {
      const result = await roiWorkflowAPI.getWorkflowResult(workflowId);
      console.log('Fetched workflow result:', result);
      await handleRealWorkflowComplete(result);
    } catch (error: any) {
      console.error('Failed to fetch workflow results:', error);
      setError('Failed to fetch workflow results');
      setPhase('error');
    }
  };

  const handleDataChange = (updatedData: ROIReportData[]) => {
    setResults(updatedData);
  };

  const handleStartOver = () => {
    // Cleanup
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Reset state
    setPhase('upload');
    setSelectedFile(null);
    setWorkflowId(null);
    setWorkflowStatus(null);
    setResults([]);
    setError(null);
    setTranscript('');
    setTranscriptEnglish('');
    setLanguage(null);
  };

  const renderCurrentPhase = () => {
    switch (phase) {
      case 'upload':
        return (
          <AudioUploader
            onFileSelect={handleFileSelect}
            onUploadStart={handleUploadStart}
            onUploadProgress={handleUploadProgress}
            onUploadComplete={handleUploadComplete}
            onUploadError={handleUploadError}
          />
        );

      case 'processing':
        return workflowStatus ? (
          <WorkflowProgress status={workflowStatus} />
        ) : (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">⚡</div>
            <h3 className="text-lg font-terminal text-terminal-cyan mb-2">Initializing...</h3>
            <p className="text-terminal-cyan/70">Setting up your audio processing workflow</p>
          </div>
        );

      case 'results':
        return (
          <div className="space-y-8">
            {/* Processing Summary */}
            <div className="p-4 border border-terminal-green/50 bg-terminal-green/10 rounded-lg">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">🎉</span>
                <h3 className="text-lg font-terminal text-terminal-green">Processing Complete!</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-terminal-green/70 mb-1">Audio File:</div>
                  <div className="text-terminal-green">{selectedFile?.name}</div>
                </div>
                <div>
                  <div className="text-terminal-green/70 mb-1">Language Detected:</div>
                  <div className="text-terminal-green">{language === 'en' ? 'English' : 'Spanish'}</div>
                </div>
                <div>
                  <div className="text-terminal-green/70 mb-1">Records Extracted:</div>
                  <div className="text-terminal-green">{results.length} contacts</div>
                </div>
              </div>
            </div>

            {/* Transcript Preview */}
            <div className="p-4 border border-terminal-cyan/30 rounded-lg bg-terminal-cyan/5">
              <h4 className="font-terminal text-terminal-cyan mb-3">Full Transcript</h4>
              {language === 'es' && (
                <div className="space-y-4">
                  <div>
                    <h5 className="text-terminal-cyan/80 text-xs uppercase mb-2">Original (Spanish):</h5>
                    <p className="text-terminal-cyan/80 text-sm italic">
                      "{transcript}"
                    </p>
                  </div>
                  <div>
                    <h5 className="text-terminal-cyan/80 text-xs uppercase mb-2">English Translation:</h5>
                    <p className="text-terminal-cyan/80 text-sm">
                      "{transcriptEnglish || 'Processing translation...'}"
                    </p>
                  </div>
                </div>
              )}
              {language === 'en' && (
                <p className="text-terminal-cyan/80 text-sm">
                  "{transcript}"
                </p>
              )}
            </div>

            {/* Results Table */}
            <ResultsTable 
              data={results}
              onDataChange={handleDataChange}
            />

            {/* Export Options */}
            <ExportOptions 
              data={results}
              workflowId={workflowId || undefined}
            />

            {/* Actions */}
            <div className="flex justify-center gap-4">
              <button
                onClick={handleStartOver}
                className="px-6 py-2 border border-terminal-cyan text-terminal-cyan font-terminal uppercase hover:bg-terminal-cyan hover:text-black transition-colors"
              >
                Process Another Recording
              </button>
            </div>
          </div>
        );

      case 'error':
        return (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">❌</div>
            <h3 className="text-lg font-terminal text-red-400 mb-2">Processing Failed</h3>
            <p className="text-red-300 mb-6">{error}</p>
            <button
              onClick={handleStartOver}
              className="px-6 py-2 bg-terminal-cyan text-black font-terminal uppercase hover:bg-terminal-cyan/80 transition-colors"
            >
              Try Again
            </button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={`w-full max-w-6xl mx-auto space-y-6 ${className}`}>
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-terminal text-terminal-cyan mb-4 uppercase">
          🎤 ROI Report Automation
        </h1>
        <p className="text-terminal-cyan/70 text-lg mb-2">
          Voice-to-Table Workflow
        </p>
        <p className="text-terminal-cyan/60 text-sm">
          Transform meeting recordings into structured ROI reports • Supports English & Spanish
        </p>
      </div>

      {/* Phase Indicator */}
      <div className="flex justify-center mb-6">
        <div className="flex space-x-4">
          {[
            { key: 'upload', label: 'Upload', icon: '📤' },
            { key: 'processing', label: 'Processing', icon: '⚡' },
            { key: 'results', label: 'Results', icon: '📊' }
          ].map(({ key, label, icon }, index) => (
            <div
              key={key}
              className={`
                flex items-center space-x-2 px-4 py-2 rounded border
                ${phase === key 
                  ? 'border-terminal-cyan bg-terminal-cyan/10 text-terminal-cyan' 
                  : index < ['upload', 'processing', 'results'].indexOf(phase)
                    ? 'border-terminal-green/50 bg-terminal-green/5 text-terminal-green'
                    : 'border-terminal-cyan/30 text-terminal-cyan/50'
                }
              `}
            >
              <span>{icon}</span>
              <span className="font-terminal text-sm uppercase">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="min-h-[400px]">
        {renderCurrentPhase()}
      </div>

      {/* Footer */}
      <div className="text-center text-xs text-terminal-cyan/60 pt-6 border-t border-terminal-cyan/20">
        <p>💡 Tip: Record a clear summary including Name, Company, Position, Discussion, Contact Type, Priority, and Action Items</p>
      </div>
    </div>
  );
} 