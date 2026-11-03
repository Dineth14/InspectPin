import { ReactNode } from 'react'
import { Icon } from './Icon'

export function Eyebrow({ children }: { children: ReactNode }) { return <p className="eyebrow">{children}</p> }
export function StatusBadge({ online, text }: { online?: boolean; text?: string }) {
  return <span className={`status-badge ${online ? 'positive' : 'neutral'}`}><i />{text ?? (online ? 'Online' : 'Offline')}</span>
}
export function EmptyState({ icon = 'inspections', title, body, action }: { icon?: 'inspections' | 'device' | 'assistant'; title: string; body: string; action?: ReactNode }) {
  return <section className="empty-state"><div className="empty-glyph"><Icon name={icon} size={29} /></div><h3>{title}</h3><p>{body}</p>{action}</section>
}
export function Skeleton({ className = '' }: { className?: string }) { return <span className={`skeleton ${className}`} aria-hidden="true" /> }
