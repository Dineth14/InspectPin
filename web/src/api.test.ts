import { describe, expect, it, vi } from 'vitest'
import { ApiClient, formatBytes, relativeTime } from './api'

describe('telemetry formatting', () => {
  it('never invents missing storage', () => expect(formatBytes(null)).toBe('Unavailable'))
  it('formats binary storage units', () => expect(formatBytes(1024 * 1024)).toBe('1.00 MB'))
  it('formats a deterministic last-seen age', () => expect(relativeTime(1000, 1120)).toBe('2m ago'))
})

it('saves an inspector note under the selected inspection and active account', async () => {
  const saved = { id: 'capture-1', note: 'Label is partly obscured.' }
  const fetch = vi.fn().mockResolvedValue(Response.json(saved))
  vi.stubGlobal('fetch', fetch)
  try {
    const api = new ApiClient('test-session')
    expect(await api.saveNote(saved.id, saved.note)).toEqual(saved)
    const [path, request] = fetch.mock.calls[0]
    expect(path).toBe('/api/v1/inspections/capture-1/note')
    expect(request.method).toBe('PATCH')
    expect(request.headers.get('Authorization')).toBe('Bearer test-session')
    expect(JSON.parse(request.body)).toEqual({ note: saved.note })
  } finally {
    vi.unstubAllGlobals()
  }
})
