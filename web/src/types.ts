export type Device = {
  id: string; name: string; model: string; firmware_version: string; hardware_revision: string
  online: boolean; last_seen: number | null; battery_percent: number | null
  battery_voltage: number | null; battery_estimated: boolean | null; charge_state: string | null
  storage_free: number | null; storage_total: number | null; sd_present: boolean | null; wifi_rssi: number | null
}

export type Finding = { category?: string; description: string; severity?: string; confidence?: string; evidence?: string }
export type Inspection = {
  id: string; device_id: string | null; created_at: number; title: string; status: string
  summary: string; findings: Finding[]; simulated: boolean; image_media_id?: string | null
  media?: { id: string; media_type: string; content_type: string; byte_size: number }[]
  voice_interactions?: { id: string; transcript: string; question: string; ai_response: string; status: string; created_at: number }[]
}

export type User = { id: string; name: string; email: string; preferences: Record<string, unknown> }
