import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../api';

describe('API Module', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  it('constructs correct payload for login', async () => {
    const mockResponse = { access_token: 't', refresh_token: 'r', role: 'fan' };
    fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockResponse),
    });

    const res = await api.login('user', 'pass');
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/auth/login'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ username: 'user', password: 'pass' }),
      })
    );
    expect(res).toEqual(mockResponse);
  });

  it('correctly propagates auth token in headers', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve([]),
    });

    await api.getZones('test-token');
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/zones'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
        }),
      })
    );
  });

  it('throws custom error details when request fails', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: 'Bad Input' }),
    });

    await expect(api.login('user', 'pass')).rejects.toThrow('Bad Input');
  });
});
