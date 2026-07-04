export enum ClassificationStatus {
  Unclassified = 'UNCLASSIFIED',
  Appreciation = 'appreciation',
  Humor = 'humor',
  Questions = 'questions',
  Criticism = 'criticism',
  PersonalExperience = 'personal experience',
  Feedback = 'feedback',
  Spam = 'spam'
}

export interface Comment {
  id: string;
  author: string;
  text: string;
  timestamp: string;
  likes: number;
  classification?: ClassificationStatus;
  confidence?: number;
}

export interface AnalysisStats {
  total: number;
  appreciation: number;
  humor: number;
  questions: number;
  criticism: number;
  personalExperience: number;
  feedback: number;
  spam: number;
}

export type ExportFormat = 'JSON' | 'CSV';

export interface AppConfig {
  url: string;
  enableClassification: boolean;
  exportFormat: ExportFormat;
}

export interface ProcessingState {
  status: 'IDLE' | 'LOADING' | 'COMPLETE' | 'ERROR';
  error?: string;
  progress?: number;
}

export interface UserNotice {
  level: 'warning' | 'error';
  message: string;
}

export interface AppReadiness {
  backendAvailable: boolean;
  backendMessage: string;
  youtubeConfigured: boolean;
  youtubeMessage: string;
  classificationAvailable: boolean;
  classificationMessage: string;
  classificationModel: string;
}
