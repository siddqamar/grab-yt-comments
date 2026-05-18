import { Comment, ClassificationStatus, AnalysisStats } from '../types';
import { MOCK_COMMENTS } from '../constants';

// Helper to generate random date
const randomDate = (start: Date, end: Date) => {
  return new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime())).toISOString();
};

const getRandomClassification = (): ClassificationStatus => {
  const rand = Math.random();
  if (rand < 0.25) return ClassificationStatus.Appreciation;
  if (rand < 0.4) return ClassificationStatus.Questions;
  if (rand < 0.55) return ClassificationStatus.Criticism;
  if (rand < 0.7) return ClassificationStatus.Feedback;
  if (rand < 0.85) return ClassificationStatus.PersonalExperience;
  if (rand < 0.95) return ClassificationStatus.Humor;
  return ClassificationStatus.Spam;
};

// Simulation of the Python Backend
export const fetchComments = async (
  url: string, 
  classify: boolean
): Promise<{ comments: Comment[], stats: AnalysisStats }> => {
  
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 2000));

  if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
    throw new Error("Invalid YouTube URL provided.");
  }

  const count = 15 + Math.floor(Math.random() * 30); // Generate between 15 and 45 comments
  const comments: Comment[] = Array.from({ length: count }).map((_, i) => {
    const text = MOCK_COMMENTS[Math.floor(Math.random() * MOCK_COMMENTS.length)];
    return {
      id: `comment-${i}-${Date.now()}`,
      author: `User_${Math.floor(Math.random() * 10000)}`,
      text: text,
      timestamp: randomDate(new Date(2023, 0, 1), new Date()),
      likes: Math.floor(Math.random() * 500),
      classification: classify ? getRandomClassification() : ClassificationStatus.Unclassified,
      confidence: classify ? 0.7 + Math.random() * 0.29 : undefined
    };
  });

  const stats: AnalysisStats = {
    total: count,
    appreciation: comments.filter(c => c.classification === ClassificationStatus.Appreciation).length,
    humor: comments.filter(c => c.classification === ClassificationStatus.Humor).length,
    questions: comments.filter(c => c.classification === ClassificationStatus.Questions).length,
    criticism: comments.filter(c => c.classification === ClassificationStatus.Criticism).length,
    personalExperience: comments.filter(c => c.classification === ClassificationStatus.PersonalExperience).length,
    feedback: comments.filter(c => c.classification === ClassificationStatus.Feedback).length,
    spam: comments.filter(c => c.classification === ClassificationStatus.Spam).length,
  };

  return { comments, stats };
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
    // CSV Header
    const headers = ['ID', 'Author', 'Date', 'Likes', 'Text', 'Classification', 'Confidence'];
    const rows = data.map(c => [
      c.id,
      c.author,
      c.timestamp,
      c.likes,
      `"${c.text.replace(/"/g, '""')}"`, // Escape quotes
      c.classification || 'N/A',
      c.confidence ? c.confidence.toFixed(2) : 'N/A'
    ]);
    content = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
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
