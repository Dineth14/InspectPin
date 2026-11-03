import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { ApiClient, ApiError, formatBytes, relativeTime } from './api'
import type { Device, Inspection, User } from './types'
import { AuthenticatedImage } from './components/AuthenticatedImage'
import { BrandIcon, BrandWordmark } from './components/Brand'
import { Icon } from './components/Icon'
import { EmptyState, Eyebrow, Skeleton, StatusBadge } from './components/Ui'

type View = 'home' | 'inspections' | 'assistant' | 'device' | 'settings'
type Theme = 'dark' | 'light'

const nav: { id: View; label: string; icon: 'home' | 'inspections' | 'assistant' | 'device' | 'settings' }[] = [
  { id: 'home', label: 'Home', icon: 'home' }, { id: 'inspections', label: 'Inspections', icon: 'inspections' },
  { id: 'assistant', label: 'Assistant', icon: 'assistant' }, { id: 'device', label: 'Device', icon: 'device' },
  { id: 'settings', label: 'Settings', icon: 'settings' },
]

function mediaId(item: Inspection) { return item.media?.find(media => media.media_type === 'image')?.id }

function Auth({ onAuth }: { onAuth: (token: string, user: User) => void }) {
  const [register, setRegister] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('')
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('')
    const values = new FormData(event.currentTarget)
    try {
      const result = await new ApiClient().auth(register ? 'register' : 'login', {
        name: String(values.get('name') ?? ''), email: String(values.get('email') ?? ''), password: String(values.get('password') ?? ''),
      }); onAuth(result.access_token, result.user)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'The secure session could not be started.') } finally { setBusy(false) }
  }
  return <main className="auth-shell">
    <section className="auth-brand"><BrandWordmark /><div className="auth-copy"><Eyebrow>WEARABLE INSPECTION INTELLIGENCE</Eyebrow>
      <h1>See the detail.<br /><em>Keep the evidence.</em></h1><p>Capture electronics, ask naturally and preserve every grounded inspection result.</p></div>
      <img src="/brand/inspectpin-device-concept.svg" alt="Conceptual InspectPin wearable device" />
      <span className="concept-label">CONCEPTUAL DEVICE VISUAL</span></section>
    <section className="auth-form-wrap"><form className="auth-card" onSubmit={submit}>
      <div className="mobile-brand"><BrandWordmark compact /></div><Eyebrow>SECURE WORKSPACE</Eyebrow><h2>{register ? 'Create your workspace' : 'Welcome back'}</h2>
      <p className="form-intro">{register ? 'Start a private inspection record linked to your devices.' : 'Continue to your connected inspection system.'}</p>
      {register && <label>Full name<input name="name" required maxLength={80} autoComplete="name" placeholder="Your name" /></label>}
      <label>Email address<input name="email" type="email" required autoComplete="email" placeholder="name@example.com" /></label>
      <label>Password<input name="password" type="password" minLength={6} required autoComplete={register ? 'new-password' : 'current-password'} placeholder="At least 6 characters" /></label>
      {error && <div className="notice error" role="alert"><Icon name="alert" />{error}</div>}
      <button className="button primary wide" disabled={busy}>{busy ? <><span className="spinner" />Connecting</> : register ? 'Create account' : 'Sign in securely'}</button>
      <button className="button quiet wide" type="button" onClick={() => { setRegister(!register); setError('') }}>{register ? 'I already have an account' : 'Create a new account'}</button>
      <p className="security-note"><Icon name="shield" size={16} /> Provider credentials stay on the backend.</p>
    </form></section>
  </main>
}

function Telemetry({ icon, label, value, detail }: { icon: 'battery' | 'storage' | 'signal'; label: string; value: string; detail: string }) {
  return <div className="telemetry"><span className="telemetry-icon"><Icon name={icon} /></span><div><small>{label}</small><strong>{value}</strong><span>{detail}</span></div></div>
}

function DeviceHero({ device, onCapture, onAsk }: { device: Device; onCapture: () => void; onAsk: () => void }) {
  const storage = device.storage_free !== null && device.storage_total ? Math.round(device.storage_free / device.storage_total * 100) : null
  const battery = device.battery_percent === null ? null : Math.round(device.battery_percent)
  return <section className="device-hero panel">
    <div className="device-visual"><img src="/brand/inspectpin-device-concept.svg" alt="Conceptual visualization of the connected InspectPin" /><span>CONCEPT VISUAL</span></div>
    <div className="device-overview"><div className="device-title"><div><Eyebrow>CONNECTED INSTRUMENT</Eyebrow><h2>{device.name}</h2><p>{device.hardware_revision} · firmware {device.firmware_version}</p></div><StatusBadge online={device.online} /></div>
      <div className="telemetry-grid">
        <Telemetry icon="battery" label="BATTERY" value={battery === null ? 'Unavailable' : `${battery}%`} detail={device.battery_estimated ? 'Voltage estimate' : device.charge_state ?? 'State unavailable'} />
        <Telemetry icon="storage" label="MICROSD" value={storage === null ? 'Unavailable' : `${storage}% free`} detail={`${formatBytes(device.storage_free)} available`} />
        <Telemetry icon="signal" label="WI-FI" value={device.wifi_rssi === null ? 'Unavailable' : `${device.wifi_rssi} dBm`} detail={`Synced ${relativeTime(device.last_seen)}`} />
      </div>
      <div className="hero-actions"><button className="button primary" onClick={onCapture} disabled={!device.online}><Icon name="camera" />Capture inspection</button><button className="button secondary" onClick={onAsk}><Icon name="mic" />Ask InspectPin</button></div>
    </div>
  </section>
}

function InspectionCard({ item, api, onOpen }: { item: Inspection; api: ApiClient; onOpen: () => void }) {
  return <button className="inspection-card" onClick={onOpen}>
    <div className="inspection-thumb"><AuthenticatedImage api={api} mediaId={mediaId(item)} alt={`Evidence for ${item.title}`} />{item.simulated && <span className="simulation-tag">SIMULATED</span>}</div>
    <div className="inspection-card-body"><div className="card-meta"><span>{new Date(item.created_at * 1000).toLocaleDateString()}</span><span className={`processing ${item.status}`}>{item.status}</span></div><h3>{item.title}</h3><p>{item.summary || 'Analysis has not completed yet.'}</p>
      <footer><span>{item.id.slice(0, 8).toUpperCase()}</span><span>Open workspace <Icon name="chevron" size={16} /></span></footer></div>
  </button>
}

function InspectionGrid({ items, api, onOpen, compact = false }: { items: Inspection[]; api: ApiClient; onOpen: (item: Inspection) => void; compact?: boolean }) {
  if (!items.length) return <EmptyState title="No inspections yet" body="Capture from a connected InspectPin or run the explicitly labelled simulator." />
  return <div className={`inspection-grid ${compact ? 'compact' : ''}`}>{items.map(item => <InspectionCard item={item} api={api} onOpen={() => onOpen(item)} key={item.id} />)}</div>
}

function Dashboard({ devices, inspections, api, onCapture, onAsk, onOpen, loading }: { devices: Device[]; inspections: Inspection[]; api: ApiClient; onCapture: (d: Device) => void; onAsk: () => void; onOpen: (i: Inspection) => void; loading: boolean }) {
  if (loading && !devices.length && !inspections.length) return <div className="dashboard-skeleton"><Skeleton className="hero-skeleton" /><Skeleton className="card-skeleton" /><Skeleton className="card-skeleton" /></div>
  return <><section className="welcome"><div><Eyebrow>INSPECTION CONTROL</Eyebrow><h1>{devices.some(device => device.online) ? 'Ready for the next detail.' : 'Your inspection record is ready.'}</h1><p>Live device values come from the backend. Simulation is always identified.</p></div><div className="record-count"><strong>{inspections.length}</strong><span>inspection{inspections.length === 1 ? '' : 's'} in view</span></div></section>
    {devices[0] ? <DeviceHero device={devices[0]} onCapture={() => onCapture(devices[0])} onAsk={onAsk} /> : <EmptyState icon="device" title="Pair an InspectPin" body="No live device data is available. Pair real hardware or use the labelled simulator." />}
    <section className="section-heading"><div><Eyebrow>RECENT EVIDENCE</Eyebrow><h2>Latest inspections</h2></div></section><InspectionGrid compact items={inspections.slice(0, 4)} api={api} onOpen={onOpen} />
  </>
}

function History({ items, api, onOpen }: { items: Inspection[]; api: ApiClient; onOpen: (i: Inspection) => void }) {
  const [query, setQuery] = useState(''), [status, setStatus] = useState('all'), [order, setOrder] = useState('newest')
  const filtered = useMemo(() => items.filter(item => (status === 'all' || item.status === status) && `${item.title} ${item.summary}`.toLowerCase().includes(query.toLowerCase())).sort((a, b) => order === 'newest' ? b.created_at - a.created_at : a.created_at - b.created_at), [items, query, status, order])
  return <><section className="page-intro"><Eyebrow>EVIDENCE LIBRARY</Eyebrow><h1>Inspection history</h1><p>Search stored images, findings and processing state.</p></section>
    <div className="library-tools"><label className="search"><Icon name="search" /><span className="sr-only">Search inspections</span><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search title or finding" /></label>
      <label><span className="sr-only">Filter status</span><select value={status} onChange={event => setStatus(event.target.value)}><option value="all">All states</option><option value="completed">Completed</option><option value="received">Received</option><option value="failed">Failed</option></select></label>
      <label><span className="sr-only">Sort inspections</span><select value={order} onChange={event => setOrder(event.target.value)}><option value="newest">Newest first</option><option value="oldest">Oldest first</option></select></label></div>
    <div className="result-summary"><span>{filtered.length} result{filtered.length === 1 ? '' : 's'}</span>{query && <button className="button quiet small" onClick={() => setQuery('')}>Clear search</button>}</div><InspectionGrid items={filtered} api={api} onOpen={onOpen} />
  </>
}

function AskForm({ inspection, api, onDone, compact = false }: { inspection: Inspection; api: ApiClient; onDone: () => Promise<void>; compact?: boolean }) {
  const [question, setQuestion] = useState(''), [status, setStatus] = useState(''), [busy, setBusy] = useState(false)
  async function submit(event: FormEvent) {
    event.preventDefault(); if (!question.trim()) return; setBusy(true); setStatus('Analyzing the selected evidence…')
    try {
      const job = await api.ask(inspection.id, question.trim())
      for (let attempt = 0; attempt < 150; attempt += 1) {
        const result = await api.processingJob(job.id)
        if (result.status === 'completed') { setQuestion(''); setStatus('Answer added to this inspection.'); await onDone(); return }
        if (result.status === 'failed') throw new Error(result.error ?? 'Assistant processing failed')
        await new Promise(resolve => setTimeout(resolve, 200))
      }
      throw new Error('Assistant timed out while waiting for the model.')
    } catch (reason) { setStatus(reason instanceof Error ? reason.message : 'Assistant failed') } finally { setBusy(false) }
  }
  return <form className={`ask-form ${compact ? 'compact' : ''}`} onSubmit={submit}><label htmlFor={`question-${inspection.id}`}>Ask about this evidence</label><div className="ask-box"><textarea id={`question-${inspection.id}`} value={question} maxLength={500} rows={compact ? 2 : 3} onChange={event => setQuestion(event.target.value)} placeholder="What visible marking can you read?" required /><button className="send" disabled={busy} aria-label="Send question">{busy ? <span className="spinner" /> : <Icon name="chevron" />}</button></div>{status && <p className="form-status" role="status">{status}</p>}</form>
}

function Workspace({ item, api, onBack, onUpdated }: { item: Inspection; api: ApiClient; onBack: () => void; onUpdated: (item: Inspection) => void }) {
  async function reload() { onUpdated(await api.inspection(item.id)) }
  return <><button className="back-button" onClick={onBack}>← Evidence library</button><header className="workspace-head"><div><Eyebrow>INSPECTION {item.id.slice(0, 8).toUpperCase()}</Eyebrow><h1>{item.title}</h1><p>{new Date(item.created_at * 1000).toLocaleString()} · {item.device_id ?? 'manual upload'}</p></div><button className="button secondary" onClick={() => api.downloadReport(item.id)}><Icon name="download" />Export report</button></header>
    {item.simulated && <div className="notice warning"><Icon name="alert" />Simulator result — not a physical inspection.</div>}
    <div className="workspace-grid"><section className="evidence-panel panel"><div className="panel-title"><div><Eyebrow>ORIGINAL EVIDENCE</Eyebrow><h2>Captured image</h2></div><span>{item.media?.find(m => m.media_type === 'image')?.byte_size ? formatBytes(item.media.find(m => m.media_type === 'image')!.byte_size) : 'Unavailable'}</span></div><div className="evidence-frame"><AuthenticatedImage api={api} mediaId={mediaId(item)} alt={`Original inspection evidence for ${item.title}`} /></div><p className="image-note">Original media is retained unchanged. Annotations appear only when the model returns real regions.</p></section>
      <section className="analysis-panel panel"><Eyebrow>AI ANALYSIS</Eyebrow><h2>{item.summary || 'Analysis pending'}</h2><div className="finding-list">{item.findings?.length ? item.findings.map((finding, index) => <article className="finding-card" key={index}><div><span>{finding.severity ?? 'observation'}</span><b>{finding.confidence ?? 'uncertainty not scored'}</b></div><p>{finding.description}</p>{finding.evidence && <small>Evidence: {finding.evidence}</small>}</article>) : <EmptyState title="No findings yet" body="The analysis has not returned structured observations." />}</div><p className="advisory"><Icon name="shield" />Visual advisory only. Verify with appropriate electrical testing and qualified personnel.</p></section>
      <aside className="conversation-panel panel"><Eyebrow>CONTEXT THREAD</Eyebrow><h2>Questions & answers</h2><div className="conversation-list">{item.voice_interactions?.length ? item.voice_interactions.map(turn => <article className="turn" key={turn.id}><div className="turn-user">{turn.question || turn.transcript}</div><div className="turn-ai"><BrandIcon /> <p>{turn.ai_response || (turn.status === 'failed' ? 'The answer failed. Try again.' : 'Processing…')}</p></div></article>) : <p className="muted">No follow-up questions yet.</p>}</div><AskForm inspection={item} api={api} onDone={reload} compact /></aside></div>
  </>
}

function Assistant({ items, api, onRefresh }: { items: Inspection[]; api: ApiClient; onRefresh: () => Promise<void> }) {
  const [selectedId, setSelectedId] = useState(items[0]?.id ?? ''), [detail, setDetail] = useState<Inspection | null>(null)
  const load = useCallback(async (id: string) => { if (id) setDetail(await api.inspection(id)) }, [api])
  useEffect(() => { if (!selectedId && items[0]) setSelectedId(items[0].id) }, [items, selectedId])
  useEffect(() => { void load(selectedId) }, [load, selectedId])
  if (!items.length) return <EmptyState icon="assistant" title="No inspection context" body="Capture or upload evidence before asking a grounded question." />
  async function updated() { await onRefresh(); await load(selectedId) }
  return <><section className="page-intro"><Eyebrow>CONTEXTUAL INTELLIGENCE</Eyebrow><h1>Ask InspectPin</h1><p>Technical answers stay bound to the selected evidence record.</p></section><div className="assistant-layout"><section className="assistant-context panel"><label>Inspection context<select value={selectedId} onChange={event => setSelectedId(event.target.value)}>{items.map(item => <option key={item.id} value={item.id}>{item.title} · {item.id.slice(0, 8)}</option>)}</select></label>{detail && <><div className="context-image"><AuthenticatedImage api={api} mediaId={mediaId(detail)} alt={`Context for ${detail.title}`} /></div><span className="context-title">{detail.title}</span><p>{detail.summary || 'No summary available.'}</p></>}</section>
    <section className="assistant-thread panel"><div className="assistant-heading"><BrandIcon /><div><h2>Inspection assistant</h2><span>Grounded to selected image</span></div></div><div className="conversation-list roomy">{detail?.voice_interactions?.length ? detail.voice_interactions.map(turn => <article className="turn" key={turn.id}><div className="turn-user">{turn.question || turn.transcript}</div><div className="turn-ai"><BrandIcon /><p>{turn.ai_response || 'Processing…'}</p></div></article>) : <div className="assistant-empty"><p>Start with a precise visual question.</p><div className="suggestions">{['What visible markings can you read?', 'Which components are clearly visible?', 'What detail needs a closer photo?'].map(text => <span key={text}>{text}</span>)}</div></div>}</div>{detail && <AskForm inspection={detail} api={api} onDone={updated} />}</section></div></>
}

function Devices({ devices, onCapture, onPair, onUnpair }: { devices: Device[]; onCapture: (d: Device) => void; onPair: () => void; onUnpair: (d: Device) => void }) {
  return <><section className="page-intro with-action"><div><Eyebrow>INSTRUMENT MANAGEMENT</Eyebrow><h1>Devices</h1><p>Identity, live telemetry and secure pairing.</p></div><button className="button primary" onClick={onPair}>Pair development device</button></section>{devices.length ? <div className="device-list">{devices.map(device => <section className="device-detail panel" key={device.id}><header><div><StatusBadge online={device.online} /><h2>{device.name}</h2><code>{device.id}</code></div><img src="/brand/inspectpin-device-concept.svg" alt="Conceptual InspectPin device" /></header><div className="spec-grid"><div><span>Hardware revision</span><strong>{device.hardware_revision}</strong></div><div><span>Firmware</span><strong>{device.firmware_version}</strong></div><div><span>Battery</span><strong>{device.battery_percent === null ? 'Unavailable' : `${Math.round(device.battery_percent)}% estimated`}</strong></div><div><span>Charge state</span><strong>{device.charge_state ?? 'Unavailable'}</strong></div><div><span>microSD</span><strong>{device.sd_present === null ? 'Unavailable' : device.sd_present ? 'Inserted' : 'Not detected'}</strong></div><div><span>Last synchronization</span><strong>{relativeTime(device.last_seen)}</strong></div></div><footer><button className="button primary" onClick={() => onCapture(device)} disabled={!device.online}><Icon name="camera" />Capture</button><button className="button danger" onClick={() => onUnpair(device)}>Unpair device</button></footer></section>)}</div> : <EmptyState icon="device" title="No device paired" body="Pairing uses the repository's real secure device registration contract. BLE discovery is not claimed." action={<button className="button primary" onClick={onPair}>Start pairing</button>} />}</>
}

function PairDialog({ onClose, onPair }: { onClose: () => void; onPair: (data: { device_id: string; name: string; model: string; hardware_revision: string; firmware_version: string }) => Promise<void> }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('')
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setBusy(true); setError(''); const data = new FormData(event.currentTarget); try { await onPair({ device_id: String(data.get('device_id')), name: String(data.get('name')), model: 'xiao_esp32s3_sense_dev', hardware_revision: 'development', firmware_version: 'unknown' }) } catch (reason) { setError(reason instanceof Error ? reason.message : 'Pairing failed'); setBusy(false) } }
  return <div className="modal-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) onClose() }}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="pair-title"><header><div><Eyebrow>SECURE OWNERSHIP</Eyebrow><h2 id="pair-title">Pair development device</h2></div><button className="icon-button" onClick={onClose} aria-label="Close"><Icon name="close" /></button></header><p>Enter the stable ID shown by firmware. BLE discovery is not available and is not simulated.</p><form onSubmit={submit}><label>Device ID<input name="device_id" pattern="[A-Za-z0-9_-]{1,64}" required placeholder="pin-dc225c8fee68" /></label><label>Device name<input name="name" maxLength={80} required placeholder="Workshop InspectPin" /></label>{error && <div className="notice error">{error}</div>}<button className="button primary wide" disabled={busy}>{busy ? 'Pairing…' : 'Confirm ownership and pair'}</button></form></section></div>
}

function Settings({ user, theme, onTheme, onLogout }: { user: User | null; theme: Theme; onTheme: (t: Theme) => void; onLogout: () => void }) {
  return <><section className="page-intro"><Eyebrow>WORKSPACE CONTROL</Eyebrow><h1>Settings</h1><p>Account, appearance, privacy and data boundaries.</p></section><div className="settings-grid"><section className="panel settings-card"><Eyebrow>ACCOUNT</Eyebrow><div className="profile-row"><span>{user?.name.slice(0, 1).toUpperCase()}</span><div><h2>{user?.name}</h2><p>{user?.email}</p></div></div></section><section className="panel settings-card"><Eyebrow>APPEARANCE</Eyebrow><h2>Interface theme</h2><div className="theme-switch"><button className={theme === 'dark' ? 'active' : ''} onClick={() => onTheme('dark')}>Midnight</button><button className={theme === 'light' ? 'active' : ''} onClick={() => onTheme('light')}>Precision light</button></div></section><section className="panel settings-card"><Eyebrow>PRIVACY</Eyebrow><h2>Your evidence remains protected</h2><p>Media access is ownership checked. AI provider credentials stay on the backend. InspectPin does not infer charging completion from battery voltage.</p></section><section className="panel settings-card danger-zone"><Eyebrow>SESSION</Eyebrow><h2>Sign out securely</h2><p>This removes the access token from the current browser session.</p><button className="button danger" onClick={onLogout}>Sign out</button></section></div></>
}

export default function App() {
  const legacy = localStorage.getItem('inspectpin_token'); if (legacy && !sessionStorage.getItem('inspectpin_token')) { sessionStorage.setItem('inspectpin_token', legacy); localStorage.removeItem('inspectpin_token') }
  const [token, setToken] = useState(() => sessionStorage.getItem('inspectpin_token') ?? ''), [user, setUser] = useState<User | null>(null)
  const [view, setView] = useState<View>('home'), [devices, setDevices] = useState<Device[]>([]), [inspections, setInspections] = useState<Inspection[]>([])
  const [selected, setSelected] = useState<Inspection | null>(null), [message, setMessage] = useState<{ text: string; kind: 'success' | 'error' } | null>(null), [loading, setLoading] = useState(false), [pairing, setPairing] = useState(false)
  const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem('inspectpin_theme') as Theme) || 'dark')
  const api = useMemo(() => new ApiClient(token), [token])
  useEffect(() => { document.documentElement.dataset.theme = theme; localStorage.setItem('inspectpin_theme', theme) }, [theme])
  const refresh = useCallback(async () => { if (!token) return; setLoading(true); try { const [me, deviceData, inspectionData] = await Promise.all([api.me(), api.devices(), api.inspections()]); setUser(me); setDevices(deviceData.items); setInspections(inspectionData.items) } catch (reason) { if (reason instanceof ApiError && reason.status === 401) { sessionStorage.removeItem('inspectpin_token'); setToken('') } else setMessage({ text: reason instanceof Error ? reason.message : 'Could not refresh', kind: 'error' }) } finally { setLoading(false) } }, [api, token])
  useEffect(() => { void refresh() }, [refresh]); useEffect(() => { const resume = () => document.visibilityState === 'visible' && void refresh(); document.addEventListener('visibilitychange', resume); return () => document.removeEventListener('visibilitychange', resume) }, [refresh])
  if (!token) return <Auth onAuth={(value, current) => { sessionStorage.setItem('inspectpin_token', value); setToken(value); setUser(current) }} />
  async function open(item: Inspection) { try { setSelected(await api.inspection(item.id)); setView('inspections') } catch (reason) { setMessage({ text: reason instanceof Error ? reason.message : 'Could not open inspection', kind: 'error' }) } }
  async function capture(device: Device) { try { await api.command(device.id, 'capture_photo'); setMessage({ text: 'Photo command queued. InspectPin will acknowledge it when online.', kind: 'success' }) } catch (reason) { setMessage({ text: reason instanceof Error ? reason.message : 'Command failed', kind: 'error' }) } }
  async function pair(input: Parameters<ApiClient['pairDevice']>[0]) { const result = await api.pairDevice(input); setPairing(false); setMessage({ text: `Paired. Copy the one-time device credential now: ${result.device_token}`, kind: 'success' }); await refresh() }
  async function unpair(device: Device) { if (!confirm(`Unpair ${device.name}? The device credential will be revoked.`)) return; await api.unpairDevice(device.id); await refresh() }
  function changeView(next: View) { setView(next); setSelected(null) }
  async function logout() { try { await api.logout() } finally { sessionStorage.removeItem('inspectpin_token'); setToken('') } }
  return <div className="app-shell"><aside className="sidebar"><div className="sidebar-brand"><BrandIcon /><BrandWordmark compact /></div><nav aria-label="Primary navigation">{nav.map(item => <button className={view === item.id ? 'active' : ''} key={item.id} onClick={() => changeView(item.id)}><Icon name={item.icon} /><span>{item.label}</span></button>)}</nav><div className="sidebar-status"><span className={devices.some(d => d.online) ? 'live' : ''} /><div><small>DEVICE NETWORK</small><strong>{devices.some(d => d.online) ? 'Instrument online' : 'No live device'}</strong></div></div><button className="account-mini" onClick={() => changeView('settings')}><span>{user?.name.slice(0, 1).toUpperCase()}</span><div><strong>{user?.name}</strong><small>{user?.email}</small></div><Icon name="chevron" /></button></aside>
    <main className="main"><header className="topbar"><div className="mobile-top-brand"><BrandWordmark compact /></div><div className="top-context"><span>{nav.find(item => item.id === view)?.label}</span><small>{devices.some(d => d.online) ? 'Live telemetry connected' : 'Backend workspace'}</small></div><div className="top-actions"><button className="icon-button" onClick={() => void refresh()} disabled={loading} aria-label="Refresh data"><Icon name="refresh" /></button><button className="avatar-button" onClick={() => changeView('settings')} aria-label="Open account settings">{user?.name.slice(0, 1).toUpperCase()}</button></div></header>
      <div className="content">{message && <div className={`notice ${message.kind}`} role="status"><Icon name={message.kind === 'error' ? 'alert' : 'shield'} />{message.text}<button onClick={() => setMessage(null)} aria-label="Dismiss"><Icon name="close" size={16} /></button></div>}
        {view === 'home' && <Dashboard devices={devices} inspections={inspections} api={api} onCapture={capture} onAsk={() => changeView('assistant')} onOpen={open} loading={loading} />}
        {view === 'inspections' && (selected ? <Workspace item={selected} api={api} onBack={() => setSelected(null)} onUpdated={setSelected} /> : <History items={inspections} api={api} onOpen={open} />)}
        {view === 'assistant' && <Assistant items={inspections} api={api} onRefresh={refresh} />}
        {view === 'device' && <Devices devices={devices} onCapture={capture} onPair={() => setPairing(true)} onUnpair={unpair} />}
        {view === 'settings' && <Settings user={user} theme={theme} onTheme={setTheme} onLogout={logout} />}
      </div></main><nav className="bottom-nav" aria-label="Mobile navigation">{nav.map(item => <button className={view === item.id ? 'active' : ''} key={item.id} onClick={() => changeView(item.id)}><Icon name={item.icon} /><span>{item.label}</span></button>)}</nav>{pairing && <PairDialog onClose={() => setPairing(false)} onPair={pair} />}</div>
}
