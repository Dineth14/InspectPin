import { describe, expect, it } from 'vitest'
import { formatBytes, relativeTime } from './api'

describe('telemetry formatting', () => {
  it('never invents missing storage', () => expect(formatBytes(null)).toBe('Unavailable'))
  it('formats binary storage units', () => expect(formatBytes(1024 * 1024)).toBe('1.00 MB'))
  it('formats a deterministic last-seen age', () => expect(relativeTime(1000, 1120)).toBe('2m ago'))
})
