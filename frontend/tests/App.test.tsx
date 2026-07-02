import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { fetchComments, fetchReadiness } from '../services/apiService';

vi.mock('../services/apiService', () => ({
  fetchComments: vi.fn(),
  fetchReadiness: vi.fn(),
  downloadData: vi.fn(),
}));

const mockedFetchComments = vi.mocked(fetchComments);
const mockedFetchReadiness = vi.mocked(fetchReadiness);

const readyReadiness = {
  backendAvailable: true,
  backendMessage: 'Backend ready.',
  youtubeConfigured: true,
  youtubeMessage: 'YouTube API key detected.',
  classificationAvailable: true,
  classificationMessage: 'Classification model server is reachable.',
  classificationModel: 'test-model',
};

describe('App readiness', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders a backend unavailable state when readiness loading fails', async () => {
    mockedFetchReadiness.mockRejectedValueOnce(
      new Error('Backend unavailable. Start the FastAPI server or launch the Electron desktop app.')
    );

    render(<App />);

    expect(await screen.findByText('Unavailable')).toBeInTheDocument();
    expect(
      screen.getByText('Backend unavailable. Start the FastAPI server or launch the Electron desktop app.')
    ).toBeInTheDocument();
  });

  it('renders missing API key and unavailable model states', async () => {
    mockedFetchReadiness.mockResolvedValueOnce({
      backendAvailable: true,
      backendMessage: 'Backend ready.',
      youtubeConfigured: false,
      youtubeMessage: 'YOUTUBE_API_KEY is missing. Set it before scraping comments.',
      classificationAvailable: false,
      classificationMessage:
        'Classification model server is unavailable at http://127.0.0.1:8080. Start the local model server or update LOCAL_LLM_URL.',
      classificationModel: 'test-model',
    });

    render(<App />);

    expect(
      await screen.findByText('YOUTUBE_API_KEY is missing. Set it before scraping comments.')
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Classification model server is unavailable/i).length).toBeGreaterThan(0);
    expect(screen.getByRole('checkbox')).toBeDisabled();

    fireEvent.change(screen.getByPlaceholderText('Paste YouTube URL here...'), {
      target: { value: 'https://www.youtube.com/watch?v=dQw4w9wg3k' },
    });
    expect(screen.getByRole('button', { name: /Run/i })).toBeDisabled();
  });

  it('renders request errors returned during scraping', async () => {
    mockedFetchReadiness.mockResolvedValueOnce(readyReadiness);
    mockedFetchComments.mockRejectedValueOnce(new Error('Invalid YouTube URL'));

    render(<App />);

    await screen.findByText('Configured');

    fireEvent.change(screen.getByPlaceholderText('Paste YouTube URL here...'), {
      target: { value: 'https://www.youtube.com/watch?v=dQw4w9wg3k' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Run/i }));

    expect(await screen.findByText('Invalid YouTube URL')).toBeInTheDocument();
  });
});
