import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { fetchComments } from '../services/apiService';

describe('apiService', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('throws error when url is empty', async () => {
    await expect(fetchComments('', false)).rejects.toThrow('YouTube URL is required');
  });

  it('calls the correct backend endpoint with classification flag', async () => {
    const mockResponse = {
      status: 'success',
      data: {
        comments: [
          { id: 'c1', author: 'User1', text: 'Nice!', timestamp: '2024', likes: 10, classification: 'appreciation' }
        ],
        stats: { total: 1, appreciation: 1, humor: 0, questions: 0, criticism: 0, 'personal experience': 0, feedback: 0, spam: 0 },
        video_title: 'Test Video',
        video_url: 'https://youtube.com/watch?v=123',
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    await fetchComments('https://youtube.com/watch?v=123', true);

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/comments'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ url: 'https://youtube.com/watch?v=123', enable_classification: true }),
      })
    );
  });

  it('throws helpful error on network failure', async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(fetchComments('https://youtube.com/watch?v=123', false))
      .rejects.toThrow('Network error: Unable to connect to the FastAPI backend.');
  });
});
