import { API_ENDPOINTS } from '../config';
import { getAuthHeaders } from './auth';

export type ExportFormat = 'csv' | 'pdf' | 'both';

export interface ExportRequest {
  rows: Record<string, any>[];
  request_id: string;
  format_type: ExportFormat;
}

export async function exportResults(
  rows: Record<string, any>[],
  requestId: string,
  format: ExportFormat = 'both'
): Promise<{ csv?: string; pdf?: string }> {
  try {
    const baseUrl = API_ENDPOINTS.ask.replace('/ask', '');
    const response = await fetch(`${baseUrl}/export`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        rows,
        request_id: requestId,
        format_type: format,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Export failed with status ${response.status}`);
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Export error:', error);
    throw error;
  }
}

/**
 * Download a file from the backend exports directory
 * @param filePath - Path returned from backend (e.g., "exports/query_123_20240101_120000.csv")
 * @param fileName - Name for the downloaded file
 */
export async function downloadFile(filePath: string, fileName: string) {
  try {
    const baseUrl = API_ENDPOINTS.ask.replace('/ask', '');
    const downloadUrl = `${baseUrl}/${filePath}`;
    
    const response = await fetch(downloadUrl, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Download failed with status ${response.status}`);
    }

    // Create a blob from the response
    const blob = await response.blob();
    
    // Create a temporary download link
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up the object URL
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Download failed:', error);
    throw error;
  }
}
