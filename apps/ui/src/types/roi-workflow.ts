// ROI Workflow Types

export interface AudioFile {
  file: File;
  url: string;
  duration?: number;
  size: number;
  format: string;
  name: string;
}

export interface WorkflowStep {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  message: string;
  progress?: number;
  estimatedTime?: number;
  startTime?: string;
  endTime?: string;
}

export interface ROIReportData {
  id: string;
  name: string;
  company: string;
  position: string;
  discussion: string;
  contactType: 'prospective' | 'existing';
  priorityLevel: 'high' | 'medium' | 'low';
  actionItems: string[];
}

export interface WorkflowResult {
  id: string;
  status: 'processing' | 'completed' | 'error' | 'failed';
  data?: ROIReportData[];
  transcript?: string;
  transcription?: string;
  transcription_english?: string;
  language?: 'en' | 'es';
  language_detected?: string;
  extracted_data?: any;
  error?: string;
  processingTime?: number;
  createdAt: string;
}

export interface WorkflowStatus {
  id: string;
  status: 'uploaded' | 'uploading' | 'transcribing' | 'extracting' | 'generating' | 'completed' | 'error' | 'failed';
  steps: WorkflowStep[];
  progress: number;
  currentStep: string;
  estimatedTimeRemaining?: number;
  error?: string;
  error_message?: string;
}

export interface ExportOptions {
  format: 'csv' | 'json' | 'pdf';
  filename?: string;
  includeHeaders?: boolean;
  selectedRows?: string[];
}

export interface AudioUploadResponse {
  id: string;
  status: 'uploaded';
  message: string;
  workflowId: string;
} 