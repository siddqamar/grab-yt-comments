import { Comment, ClassificationStatus, AnalysisStats } from '../types';

const configuredApiUrl = import.meta.env.VITE_API_URL;
const API_URL =
  configuredApiUrl && !configuredApiUrl.includes('REPLACE_WITH')
    ? configuredApiUrl
    : 'http://localhost:8000';

// Backend API response types
interface BackendComment {
  id: string;
  author: string;
  text: string;
  timestamp: string;
  likes: number;
  classification?: string;
}

interface BackendResponse {
  status: string;
  data: {
    comments: BackendComment[];
    stats: {
      total: number;
      appreciation: number;
      humor: number;
      questions: number;
      criticism: number;
      'personal experience': number;
      feedback: number;
      spam: number;
    };
    video_title: string;
    video_url: string;
  };
}

interface ErrorResponse {
  detail?: string;
  error?: {
    message?: string;
  };
}

/**
 * Fetch comments from YouTube video using the backend API
 * @param url - YouTube video URL
 * @param classify - Whether to enable classification
 * @returns Promise with comments and stats
 */
export const fetchComments = async (
  url: string,
  classify: boolean
): Promise<{ comments: Comment[]; stats: AnalysisStats }> => {
  // Validate inputs
  if (!url) {
    throw new Error('YouTube URL is required');
  }

  try {
    const response = await fetch(`${API_URL}/api/v1/comments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: url,
        enable_classification: classify,
      }),
    });

    // Handle HTTP errors
    if (!response.ok) {
      const errorData: ErrorResponse = await response.json();
      throw new Error(
        errorData.detail ||
          errorData.error?.message ||
          `HTTP ${response.status}: ${response.statusText}`
      );
    }

    // Parse successful response
    const data: BackendResponse = await response.json();

    // Transform backend comments to frontend format
    const comments: Comment[] = data.data.comments.map((comment, index) => {
      let classification = ClassificationStatus.Unclassified;
      if (classify && comment.classification) {
        const normalized = comment.classification.toLowerCase() as ClassificationStatus;
        if (Object.values(ClassificationStatus).includes(normalized)) {
          classification = normalized;
        }
      }

      return {
        id: comment.id || `comment-${index}-${Date.now()}`,
        author: comment.author,
        text: comment.text,
        timestamp: comment.timestamp,
        likes: comment.likes,
        classification: classification,
      };
    });

    const stats: AnalysisStats = {
      total: data.data.stats.total,
      appreciation: data.data.stats.appreciation,
      humor: data.data.stats.humor,
      questions: data.data.stats.questions,
      criticism: data.data.stats.criticism,
      personalExperience: data.data.stats['personal experience'],
      feedback: data.data.stats.feedback,
      spam: data.data.stats.spam,
    };

    return { comments, stats };
  } catch (error) {
    // Enhanced error handling
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to the FastAPI backend.');
    }

    if (error instanceof Error) {
      throw error;
    }

    throw new Error('An unexpected error occurred while fetching comments.');
  }
};

/**
 * Download comments data as JSON or CSV
 * @param data - Array of comments to download
 * @param format - Export format (JSON or CSV)
 */
export const downloadData = (data: Comment[], format: 'JSON' | 'CSV') => {
  let content = '';
  let mimeType = '';
  let extension = '';

  if (format === 'JSON') {
    content = JSON.stringify(data, null, 2);
    mimeType = 'application/json';
    extension = 'json';
  } else {
    // CSV Header
    const headers = ['ID', 'Author', 'Date', 'Likes', 'Text', 'Classification'];
    const rows = data.map((c) => [
      c.id,
      c.author,
      c.timestamp,
      c.likes,
      `"${c.text.replace(/"/g, '""')}"`, // Escape quotes
      c.classification || 'N/A',
    ]);
    content = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    mimeType = 'text/csv';
    extension = 'csv';
  }

  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `comments_export_${Date.now()}.${extension}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

/**
 * Check API health status
 * @returns Promise with health check result
 */
export const checkApiHealth = async (): Promise<boolean> => {
  if (!API_URL) return false;

  try {
    const response = await fetch(`${API_URL}/health`, {
      method: 'GET',
    });
    return response.ok;
  } catch {
    return false;
  }
};
