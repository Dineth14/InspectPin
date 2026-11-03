import type { Device, Inspection, User } from './types'

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message) }
}

export class ApiClient {
  constructor(public token = '', public base = '') {}
  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers)
    if (this.token) headers.set('Authorization', `Bearer ${this.token}`)
    if (init.body && typeof init.body === 'string') headers.set('Content-Type', 'application/json')
    const response = await fetch(this.base + path, { ...init, headers })
    if (!response.ok) {
      let payload: { error?: { code?: string; message?: string } } = {}
      try { payload = await response.json() } catch { /* response is not JSON */ }
      throw new ApiError(response.status, payload.error?.code ?? 'HTTP_ERROR', payload.error?.message ?? response.statusText)
    }
    if (response.status === 204) return undefined as T
    return response.json() as Promise<T>
  }
  auth(mode: 'login' | 'register', body: Record<string, string>) {
    return this.request<{ access_token: string; user: User }>(`/api/v1/auth/${mode}`, { method: 'POST', body: JSON.stringify(body) })
  }
  me() { return this.request<User>('/api/v1/auth/me') }
  logout() { return this.request<void>('/api/v1/auth/logout', { method: 'POST' }) }
  devices() { return this.request<{ items: Device[] }>('/api/v1/devices') }
  inspections() { return this.request<{ items: Inspection[]; total: number }>('/api/v1/inspections?limit=50') }
  inspection(id: string) { return this.request<Inspection>(`/api/v1/inspections/${id}`) }
  command(device: string, type: string, payload: Record<string, unknown> = {}) {
    return this.request(`/api/v1/devices/${device}/commands`, { method: 'POST', body: JSON.stringify({ type, payload }) })
  }
  ask(inspection: string, question: string) {
    return this.request<{ id: string; status: string; interaction_id: string }>(`/api/v1/inspections/${inspection}/questions`, {
      method: 'POST', body: JSON.stringify({ question }), headers: { 'Idempotency-Key': crypto.randomUUID() },
    })
  }
  processingJob(id: string) { return this.request<{ status: string; error: string | null }>(`/api/v1/processing-jobs/${id}`) }
  async downloadReport(id: string) {
    const response = await fetch(this.base + `/api/v1/inspections/${id}/report`, { headers: { Authorization: `Bearer ${this.token}` } })
    if (!response.ok) throw new ApiError(response.status, 'REPORT_FAILED', 'Report download failed')
    const url = URL.createObjectURL(await response.blob())
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = `inspectpin-${id}.pdf`; anchor.click()
    URL.revokeObjectURL(url)
  }
}

export function formatBytes(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return 'Unavailable'
  if (value < 1024) return `${value} B`
  const units = ['KB', 'MB', 'GB', 'TB']; let size = value; let index = -1
  do { size /= 1024; index += 1 } while (size >= 1024 && index < units.length - 1)
  return `${size.toFixed(size >= 10 ? 1 : 2)} ${units[index]}`
}

export function relativeTime(epoch: number | null, now = Date.now() / 1000): string {
  if (!epoch) return 'Never'
  const seconds = Math.max(0, Math.round(now - epoch))
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  return `${Math.floor(seconds / 3600)}h ago`
}
