export function BrandWordmark({ compact = false }: { compact?: boolean }) {
  return <span className={`brand-wordmark ${compact ? 'compact' : ''}`} aria-label="InspectPin AI">
    <span>Inspect</span><span className="brand-cyan">Pin</span><span className="brand-ai">AI</span><i aria-hidden="true" />
  </span>
}

export function BrandIcon() {
  return <span className="brand-icon" aria-label="InspectPin AI"><b>I</b><b>P</b><i /></span>
}
