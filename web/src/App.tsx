import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { ApiClient, ApiError, formatBytes, relativeTime } from './api'
import type { Device, Inspection, User } from './types'

type View = 'dashboard' | 'devices' | 'inspections' | 'assistant' | 'settings'

function Auth({ onAuth }: { onAuth: (token: string, user: User) => void }) {
  const [register, setRegister] = useState(false), [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('')
    const values = new FormData(event.currentTarget)
    try {
      const result = await new ApiClient().auth(register ? 'register' : 'login', {
        name: String(values.get('name') ?? ''), email: String(values.get('email') ?? ''), password: String(values.get('password') ?? ''),
      }); onAuth(result.access_token, result.user)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Sign-in failed') } finally { setBusy(false) }
  }
  return <main className="auth-shell">
    <section className="brand-panel"><div className="pin-mark">IP</div><p className="eyebrow">WEARABLE INSPECTION INTELLIGENCE</p>
      <h1>See the detail.<br /><span>Keep the evidence.</span></h1>
      <p>InspectPin combines camera, voice and grounded AI assistance while preserving the original inspection record.</p></section>
    <form className="auth-card" onSubmit={submit}>
      <p className="eyebrow">SECURE WORKSPACE</p><h2>{register ? 'Create account' : 'Welcome back'}</h2>
      {register && <label>Name<input name="name" required maxLength={80} autoComplete="name" /></label>}
      <label>Email<input name="email" type="email" required autoComplete="email" /></label>
      <label>Password<input name="password" type="password" minLength={6} required autoComplete={register ? 'new-password' : 'current-password'} /></label>
      {error && <div className="alert error" role="alert">{error}</div>}
      <button className="primary" disabled={busy}>{busy ? 'Connecting…' : register ? 'Create account' : 'Sign in'}</button>
      <button className="text-button" type="button" onClick={() => setRegister(!register)}>{register ? 'Use an existing account' : 'Create a new account'}</button>
    </form>
  </main>
}

function StatusPill({ online }: { online: boolean }) { return <span className={`pill ${online ? 'online' : 'offline'}`}><i />{online ? 'Online' : 'Offline'}</span> }

function DeviceCard({ device, onCapture }: { device: Device; onCapture: () => void }) {
  const storage = device.storage_free !== null && device.storage_total ? Math.round(device.storage_free / device.storage_total * 100) : null
  return <article className="panel device-card">
    <header><div><p className="eyebrow">PRIMARY DEVICE</p><h3>{device.name}</h3></div><StatusPill online={device.online} /></header>
    <div className="metrics">
      <div><span>BATTERY</span><strong>{device.battery_percent === null ? '—' : `${Math.round(device.battery_percent)}%`}</strong><small>{device.battery_estimated ? 'Voltage estimate' : device.charge_state ?? 'Unavailable'}</small></div>
      <div><span>STORAGE</span><strong>{storage === null ? '—' : `${storage}%`}</strong><small>{formatBytes(device.storage_free)} free</small></div>
      <div><span>SIGNAL</span><strong>{device.wifi_rssi === null ? '—' : `${device.wifi_rssi}`}</strong><small>{device.wifi_rssi === null ? 'Unavailable' : 'dBm'}</small></div>
    </div>
    <footer><span>Last seen {relativeTime(device.last_seen)}</span><button onClick={onCapture} disabled={!device.online}>Request photo</button></footer>
  </article>
}

function InspectionList({ items, onOpen }: { items: Inspection[]; onOpen: (item: Inspection) => void }) {
  if (!items.length) return <div className="empty">No inspections yet. Capture from a paired device or run the simulator.</div>
  return <div className="inspection-grid">{items.map(item => <button className="inspection-card" key={item.id} onClick={() => onOpen(item)}>
    <div className="thumbnail">{item.simulated ? 'SIM' : 'IMG'}</div><div><div className="row"><strong>{item.title}</strong><span className={`status ${item.status}`}>{item.status}</span></div>
      <p>{item.summary || 'Awaiting analysis'}</p><small>{new Date(item.created_at * 1000).toLocaleString()} · {item.id.slice(0, 8)}</small></div>
  </button>)}</div>
}

function InspectionDetail({ item, onBack, api }: { item: Inspection; onBack: () => void; api: ApiClient }) {
  return <section><button className="back" onClick={onBack}>← All inspections</button>
    <div className="detail-head"><div><p className="eyebrow">INSPECTION {item.id.slice(0, 8).toUpperCase()}</p><h2>{item.title}</h2></div>
      <button onClick={() => api.downloadReport(item.id)}>Download PDF report</button></div>
    {item.simulated && <div className="alert warning">Simulator data — this is not a physical inspection result.</div>}
    <div className="detail-layout"><article className="panel media-panel"><h3>Original evidence</h3>
      <div className="image-placeholder">Protected image · {item.media?.find(media => media.media_type === 'image')?.byte_size ?? 0} bytes</div></article>
      <article className="panel"><p className="eyebrow">ANALYSIS</p><h3>{item.summary || 'Analysis pending'}</h3>
        {(item.findings ?? []).map((finding, index) => <div className="finding" key={index}><span>{finding.severity ?? 'observation'}</span><p>{finding.description}</p><small>{finding.evidence}</small></div>)}
        <p className="disclaimer">Advisory visual analysis only. It does not replace electrical testing or qualified safety inspection.</p></article></div>
  </section>
}

function Assistant({ items, api, onDone }: { items: Inspection[]; api: ApiClient; onDone: () => Promise<void> }) {
  const [inspection, setInspection] = useState(items[0]?.id ?? ''), [question, setQuestion] = useState('')
  const [status, setStatus] = useState(''), [busy, setBusy] = useState(false)
  async function ask(event: FormEvent) {
    event.preventDefault(); if (!inspection || !question.trim()) return; setBusy(true); setStatus('Question queued…')
    try {
      const job = await api.ask(inspection, question.trim())
      for (let attempt = 0; attempt < 150; attempt += 1) {
        const result = await api.processingJob(job.id)
        if (result.status === 'completed') { setStatus('Answer stored in the inspection timeline.'); setQuestion(''); await onDone(); return }
        if (result.status === 'failed') throw new Error(result.error ?? 'Assistant processing failed')
        await new Promise(resolve => setTimeout(resolve, 200))
      }
      throw new Error('Assistant timed out')
    } catch (reason) { setStatus(reason instanceof Error ? reason.message : 'Assistant failed') } finally { setBusy(false) }
  }
  if (!items.length) return <div className="empty">Capture or upload an inspection before asking a grounded question.</div>
  return <form className="panel settings" onSubmit={ask}><p className="eyebrow">CONTEXTUAL ASSISTANT</p><h2>Ask about an inspection</h2>
    <label>Inspection<select value={inspection} onChange={event => setInspection(event.target.value)}>{items.map(item => <option key={item.id} value={item.id}>{item.title} · {item.id.slice(0, 8)}</option>)}</select></label>
    <label>Question<textarea value={question} maxLength={500} rows={4} onChange={event => setQuestion(event.target.value)} placeholder="What visible marking can you read?" required /></label>
    {status && <div className="alert success" role="status">{status}</div>}<button className="primary" disabled={busy}>{busy ? 'Analyzing…' : 'Ask InspectPin'}</button>
    <p className="disclaimer">Answers are bound to the selected stored image and remain advisory.</p></form>
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('inspectpin_token') ?? '')
  const [user, setUser] = useState<User | null>(null), [view, setView] = useState<View>('dashboard')
  const [devices, setDevices] = useState<Device[]>([]), [inspections, setInspections] = useState<Inspection[]>([])
  const [selected, setSelected] = useState<Inspection | null>(null), [error, setError] = useState(''), [loading, setLoading] = useState(false)
  const api = useMemo(() => new ApiClient(token), [token])
  const refresh = useCallback(async () => {
    if (!token) return; setLoading(true); setError('')
    try { const [me, deviceData, inspectionData] = await Promise.all([api.me(), api.devices(), api.inspections()]); setUser(me); setDevices(deviceData.items); setInspections(inspectionData.items) }
    catch (reason) { if (reason instanceof ApiError && reason.status === 401) { localStorage.removeItem('inspectpin_token'); setToken('') } else setError(reason instanceof Error ? reason.message : 'Could not refresh') }
    finally { setLoading(false) }
  }, [api, token])
  useEffect(() => { void refresh() }, [refresh])
  useEffect(() => { const resume = () => { if (document.visibilityState === 'visible') void refresh() }; document.addEventListener('visibilitychange', resume); return () => document.removeEventListener('visibilitychange', resume) }, [refresh])
  if (!token) return <Auth onAuth={(value, current) => { localStorage.setItem('inspectpin_token', value); setToken(value); setUser(current) }} />
  const open = async (item: Inspection) => { try { setSelected(await api.inspection(item.id)); setView('inspections') } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not open inspection') } }
  const capture = async (device: Device) => { try { await api.command(device.id, 'capture_photo'); setError('Photo command queued. The device will acknowledge it when online.') } catch (reason) { setError(reason instanceof Error ? reason.message : 'Command failed') } }
  return <div className="app-shell"><aside><div className="logo"><span>IP</span><strong>InspectPin <em>AI</em></strong></div>
    <nav aria-label="Main navigation">{(['dashboard', 'devices', 'inspections', 'assistant', 'settings'] as View[]).map(item => <button className={view === item ? 'active' : ''} key={item} onClick={() => { setView(item); setSelected(null) }}>{item}</button>)}</nav>
    <div className="account"><span>{user?.name.slice(0, 1).toUpperCase()}</span><div><strong>{user?.name}</strong><small>{user?.email}</small></div></div></aside>
    <main className="content"><header className="topbar"><div><p className="eyebrow">INSPECTPIN CONTROL</p><h1>{view[0].toUpperCase() + view.slice(1)}</h1></div>
      <button onClick={() => void refresh()} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh'}</button></header>
      {error && <div className={`alert ${error.startsWith('Photo command') ? 'success' : 'error'}`} role="status">{error}<button onClick={() => setError('')}>×</button></div>}
      {view === 'dashboard' && <><section className="hero"><div><p className="eyebrow">SYSTEM OVERVIEW</p><h2>{devices.some(d => d.online) ? 'Your inspection system is ready.' : 'Waiting for an InspectPin device.'}</h2><p>Telemetry and results shown here come from the backend. Simulator records are labelled.</p></div><div className="hero-stat"><strong>{inspections.length}</strong><span>recent inspections</span></div></section>
        {devices[0] ? <DeviceCard device={devices[0]} onCapture={() => void capture(devices[0])} /> : <div className="empty">No paired device. Run the simulator bootstrap or pair hardware through the API.</div>}
        <section className="section-head"><div><p className="eyebrow">RECENT ACTIVITY</p><h2>Inspection history</h2></div><button onClick={() => setView('inspections')}>View all</button></section><InspectionList items={inspections.slice(0, 6)} onOpen={item => void open(item)} /></>}
      {view === 'devices' && <section><div className="section-head"><div><p className="eyebrow">HARDWARE</p><h2>Paired devices</h2></div></div>{devices.map(device => <DeviceCard key={device.id} device={device} onCapture={() => void capture(device)} />)}{!devices.length && <div className="empty">No paired devices.</div>}</section>}
      {view === 'inspections' && (selected ? <InspectionDetail item={selected} onBack={() => setSelected(null)} api={api} /> : <><div className="section-head"><div><p className="eyebrow">EVIDENCE LIBRARY</p><h2>{inspections.length} inspections</h2></div></div><InspectionList items={inspections} onOpen={item => void open(item)} /></>)}
      {view === 'assistant' && <Assistant items={inspections} api={api} onDone={refresh} />}
      {view === 'settings' && <section className="panel settings"><p className="eyebrow">ACCOUNT & PRIVACY</p><h2>{user?.name}</h2><p>{user?.email}</p><hr /><p>Media access is ownership-protected. Provider credentials stay on the backend and are never sent to this browser.</p><button className="danger" onClick={async () => { try { await api.logout() } finally { localStorage.removeItem('inspectpin_token'); setToken('') } }}>Sign out</button></section>}
    </main></div>
}
