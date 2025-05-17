import { apiClient } from './client';

export interface FileUploadResponse {
  fileId: string;
  status: string;
  uploadUrl?: string;
}

export interface FileInfo {
  id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  size: number;
  contentType: string;
  createdAt: string;
  processedAt?: string;
  knowledgeId?: string;
  error?: string;
}

export const filesAPI = {
  // Initiate file upload
  initiateUpload: async (
    filename: string,
    contentType: string,
    sizeBytes: number
  ): Promise<FileUploadResponse> => {
    const { data } = await apiClient.post('/api/v1/files/ingest', null, {
      params: {
        filename,
        content_type: contentType,
        size_bytes: sizeBytes,
      }
    });
    return data;
  },

  // Upload file directly to storage using presigned URL
  uploadToStorage: async (uploadUrl: string, file: File): Promise<void> => {
    await fetch(uploadUrl, {
      method: 'PUT',
      body: file,
      headers: {
        'Content-Type': file.type,
      },
    });
  },

  // Get file status
  getFileStatus: async (fileId: string): Promise<FileInfo> => {
    const { data } = await apiClient.get(`/api/v1/status/file/${fileId}`);
    return data;
  },

  // List user files
  listFiles: async (): Promise<FileInfo[]> => {
    const { data } = await apiClient.get('/api/v1/files');
    return data;
  },

  // Complete upload process
  uploadFile: async (file: File): Promise<FileInfo> => {
    // 1. Initiate upload and get presigned URL
    const { fileId, uploadUrl } = await filesAPI.initiateUpload(
      file.name,
      file.type,
      file.size
    );

    // 2. Upload file to storage
    if (uploadUrl) {
      await filesAPI.uploadToStorage(uploadUrl, file);
    }

    // 3. Get file status
    const fileInfo = await filesAPI.getFileStatus(fileId);
    return fileInfo;
  },
};