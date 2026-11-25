import { useState } from 'react'
import type { ApiClient } from '../api'
import type { Device, DeviceSoundSettings } from '../types'

const groups = [
  'Enable notifications', 'Startup and connection', 'Photo and image upload', 'Voice guidance',
  'Audio recording', 'Video recording', 'Warnings and errors',
]

export function DeviceSound({ api, device }: { api: ApiClient; device: Device }) {
  const [requested, setRequested] = useState<DeviceSoundSettings | null>(device.sound_settings ?? null)
  const [confirmed, setConfirmed] = useState(requested)
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)

  async function send(type: string, payload: Record<string, number> = {}) {
    setBusy(true)
    try {
      let current = await api.command(device.id, type, payload)
      for (let i = 0; i < 61 && ['pending', 'accepted'].includes(current.status); i++) {
        setStatus(`Command ${current.status}`)
        await new Promise(resolve => setTimeout(resolve, 2000))
        current = await api.commandStatus(current.id)
      }
      if (current.status === 'completed' && current.result?.sound_settings) {
        setRequested(current.result.sound_settings)
        setConfirmed(current.result.sound_settings)
      }
      setStatus(`Command ${current.status}${current.result?.error ? ' · ' + current.result.error : ''}`)
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Device command failed')
    } finally {
      setBusy(false)
    }
  }

  if (!requested || !confirmed) return <p>Waiting for device sound settings.</p>
  return <details className="inspection-actions">
    <summary>Sound & feedback</summary>
    <p>Device confirmed {confirmed.volume}% notifications and {confirmed.speech_volume}% AI speech.</p>
    <fieldset disabled={busy}>
      <legend>Requested settings</legend>
      {groups.map((title, index) => {
        const bit = 1 << index
        return <p key={title}><label><input type="checkbox" checked={(requested.groups & bit) !== 0}
          onChange={event => setRequested({ ...requested, groups: event.target.checked ? requested.groups | bit : requested.groups & ~bit })} /> {title}</label></p>
      })}
      <p><label>Notification volume <input type="range" min="0" max="100" value={requested.volume}
        onChange={event => setRequested({ ...requested, volume: Number(event.target.value) })} /> {requested.volume}%</label></p>
      <p><label>AI speech volume <input type="range" min="0" max="100" value={requested.speech_volume}
        onChange={event => setRequested({ ...requested, speech_volume: Number(event.target.value) })} /> {requested.speech_volume}%</label></p>
      <div className="hero-actions">
        <button className="button secondary" onClick={() => send('set_sound', { groups: requested.groups, volume: requested.volume })}>Save notifications</button>
        <button className="button secondary" onClick={() => send('set_volume', { percent: requested.speech_volume })}>Save AI speech volume</button>
        <button className="button secondary" onClick={() => send('test_sound')}>Test saved sound</button>
        <button className="button secondary" onClick={() => send('set_sound', { groups: 127, volume: 65 })}>Restore notification defaults</button>
      </div>
    </fieldset>
    {status && <p role="status">{status}</p>}
  </details>
}
