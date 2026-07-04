/// <reference types="vite/client" />
import {
  Comment,
  ClassificationStatus,
  AnalysisStats,
  AppReadiness,
  UserNotice,
} from '../types';

const configuredApiUrl = import.meta.env.VITE_API_URL;
const DEFAULT_API_URL = 'http://localhost:8000';

declare global {
  interface Window {
    desktopConfig?: {
      apiBaseUrl?: string;
    };
  }
}

export const resolveApiUrl = (): string => {
  const desktopApiUrl = window.desktopConfig?.apiBaseUrl;
  if (desktopApiUrl) {
    return desktopApiUrl;
  }

  if (configuredApiUrl && !configuredApiUrl.includes('REPLACE_WITH')) {
    return configuredApiUrl;
  }

  return DEFAULT_API_URL;
};

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
  meta?: {
    classification?: {
      requested: boolean;
      applied: boolean;
      status: string;
      message?: string;
    };
  };
}

interface ReadinessResponse {
  status: string;
  data: {
    backend: {
      available: boolean;
      message: string;
    };
    youtube: {
      configured: boolean;
      message: string;
    };
    classification: {
      available: boolean;
      message: string;
      model: string;
    };
  };
}

interface ErrorResponse {
  detail?: string;
  error?: {
    message?: string;
  };
}

export const fetchComments = async (
  url: string,
  classify: boolean
): Promise<{ comments: Comment[]; stats: AnalysisStats; notice?: UserNotice }> => {
  if (!url) {
    throw new Error('YouTube URL is required');
  }

  try {
    const response = await fetch(`${resolveApiUrl()}/api/v1/comments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: url,
        enable_classification: classify,
      }),
    });

    if (!response.ok) {
      const errorData: ErrorResponse = await response.json();
      throw new Error(
        errorData.detail ||
          errorData.error?.message ||
          `HTTP ${response.status}: ${response.statusText}`
      );
    }

    const data: BackendResponse = await response.json();

    const comments: Comment[] = data.data.comments.map((comment, index) => {
      let classification: ClassificationStatus | undefined;
      if (classify && comment.classification) {
        const normalized = comment.classification.toLowerCase() as ClassificationStatus;
        if (Object.values(ClassificationStatus).includes(normalized)) {
          classification = normalized;
        } else {
          classification = ClassificationStatus.Unclassified;
        }
      }

      return {
        id: comment.id || `comment-${index}-${Date.now()}`,
        author: comment.author,
        text: comment.text,
        timestamp: comment.timestamp,
        likes: comment.likes,
        classification,
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

    const classificationMeta = data.meta?.classification;
    const notice =
      classify && classificationMeta && !classificationMeta.applied
        ? {
            level: 'warning' as const,
            message:
              classificationMeta.message ||
              'Classification is unavailable. Comments were scraped without AI labels.',
          }
        : undefined;

    return { comments, stats, notice };
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to the FastAPI backend.');
    }

    if (error instanceof Error) {
      throw error;
    }

    throw new Error('An unexpected error occurred while fetching comments.');
  }
};

export const fetchReadiness = async (): Promise<AppReadiness> => {
  try {
    const response = await fetch(`${resolveApiUrl()}/api/v1/readiness`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error('Unable to load backend readiness state.');
    }

    const data: ReadinessResponse = await response.json();

    return {
      backendAvailable: data.data.backend.available,
      backendMessage: data.data.backend.message,
      youtubeConfigured: data.data.youtube.configured,
      youtubeMessage: data.data.youtube.message,
      classificationAvailable: data.data.classification.available,
      classificationMessage: data.data.classification.message,
      classificationModel: data.data.classification.model,
    };
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(
        'Backend unavailable. Start the FastAPI server or launch the Electron desktop app.'
      );
    }

    if (error instanceof Error) {
      throw error;
    }

    throw new Error('Unable to load backend readiness state.');
  }
};

export const downloadData = (data: Comment[], format: 'JSON' | 'CSV') => {
  let content = '';
  let mimeType = '';
  let extension = '';

  if (format === 'JSON') {
    content = JSON.stringify(data, null, 2);
    mimeType = 'application/json';
    extension = 'json';
  } else {
    const headers = ['ID', 'Author', 'Date', 'Likes', 'Text', 'Classification'];
    const rows = data.map((c) => [
      c.id,
      c.author,
      c.timestamp,
      c.likes,
      `"${c.text.replace(/"/g, '""')}"`,
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

export const checkApiHealth = async (): Promise<boolean> => {
  const apiUrl = resolveApiUrl();
  if (!apiUrl) return false;

  try {
    const response = await fetch(`${apiUrl}/health`, {
      method: 'GET',
    });
    return response.ok;
  } catch {
    return false;
  }
};
