import axios from 'axios';
import { 
  AudioUploadResponse, 
  WorkflowResult, 
  WorkflowStatus,
  ROIReportData 
} from '../types/roi-workflow';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';

class ROIWorkflowAPI {
  private getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async uploadAudio(file: File, onProgress?: (progress: number) => void): Promise<AudioUploadResponse> {
    const formData = new FormData();
    formData.append('audio_file', file);
    formData.append('workflow_type', 'roi_report');

    try {
      const response = await axios.post(`${API_BASE}/roi/upload`, formData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        }
      });

      return response.data;
    } catch (error: any) {
      console.error('Audio upload failed:', error);
      throw new Error(error.response?.data?.message || 'Failed to upload audio file');
    }
  }

  async uploadRecording(recordingBlob: Blob, onProgress?: (progress: number) => void): Promise<AudioUploadResponse> {
    const formData = new FormData();
    formData.append('audio_data', recordingBlob, 'recording.webm');

    try {
      const response = await axios.post(`${API_BASE}/roi/record`, formData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        }
      });

      return response.data;
    } catch (error: any) {
      console.error('Recording upload failed:', error);
      throw new Error(error.response?.data?.message || 'Failed to upload recording');
    }
  }

  async getWorkflowStatus(workflowId: string): Promise<WorkflowStatus> {
    try {
      const response = await axios.get(`${API_BASE}/roi/status/${workflowId}`, {
        headers: this.getAuthHeaders()
      });

      return response.data;
    } catch (error: any) {
      console.error('Failed to get workflow status:', error);
      throw new Error(error.response?.data?.message || 'Failed to get workflow status');
    }
  }

  async getWorkflowResult(workflowId: string): Promise<WorkflowResult> {
    try {
      const response = await axios.get(`${API_BASE}/roi/status/${workflowId}`, {
        headers: this.getAuthHeaders()
      });

      return response.data;
    } catch (error: any) {
      console.error('Failed to get workflow result:', error);
      throw new Error(error.response?.data?.message || 'Failed to get workflow result');
    }
  }

  // Poll for workflow completion
  async pollWorkflowStatus(
    workflowId: string, 
    onStatusUpdate: (status: any) => void,
    onComplete: (result: any) => void,
    maxRetries: number = 60,
    intervalMs: number = 2000
  ): Promise<void> {
    let retries = 0;
    
    const poll = async () => {
      try {
        const status = await this.getWorkflowStatus(workflowId);
        onStatusUpdate(status);
        
        // Check if completed
        if (status.status === 'completed') {
          onComplete(status);
          return;
        }
        
        // Check if failed
        if (status.status === 'failed') {
          // Don't throw error, let onComplete handle the failed status
          onComplete(status);
          return;
        }
        
        // Continue polling if not complete and retries remaining
        if (retries < maxRetries) {
          retries++;
          setTimeout(poll, intervalMs);
        } else {
          throw new Error('Workflow processing timeout');
        }
        
      } catch (error: any) {
        console.error('Polling error:', error);
        // Don't throw, just call onComplete with error status
        onComplete({
          id: workflowId,
          status: 'failed',
          error: error.message || 'Polling failed'
        });
      }
    };
    
    // Start polling
    poll();
  }

  async exportResults(workflowId: string, format: 'csv' | 'json'): Promise<Blob> {
    try {
      const response = await axios.get(`${API_BASE}/workflows/roi-report/${workflowId}/export`, {
        headers: this.getAuthHeaders(),
        params: { format },
        responseType: 'blob'
      });

      return response.data;
    } catch (error: any) {
      console.error('Failed to export results:', error);
      throw new Error(error.response?.data?.message || 'Failed to export results');
    }
  }

  // WebSocket connection for real-time updates
  connectWebSocket(workflowId: string, onMessage: (status: WorkflowStatus) => void): WebSocket {
    const token = localStorage.getItem('authToken');
    const wsUrl = `${process.env.REACT_APP_WS_URL || 'ws://localhost:8000'}/ws/workflow/${workflowId}?token=${token}`;
    
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected for workflow:', workflowId);
    };

    ws.onmessage = (event) => {
      try {
        const status: WorkflowStatus = JSON.parse(event.data);
        onMessage(status);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed');
    };

    return ws;
  }

  // Utility methods
  async validateAudioFile(file: File): Promise<{ valid: boolean; error?: string }> {
    const supportedFormats = ['audio/mpeg', 'audio/mp4', 'audio/wav', 'audio/webm'];
    const maxSize = 100 * 1024 * 1024; // 100MB

    if (!supportedFormats.includes(file.type)) {
      return { 
        valid: false, 
        error: 'Unsupported audio format. Please use MP3, M4A, WAV, or WEBM files.' 
      };
    }

    if (file.size > maxSize) {
      return { 
        valid: false, 
        error: 'File size too large. Maximum file size is 100MB.' 
      };
    }

    return { valid: true };
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  formatDuration(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }
}

export const roiWorkflowAPI = new ROIWorkflowAPI(); 