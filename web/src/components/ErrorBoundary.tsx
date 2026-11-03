import { Component, ErrorInfo, ReactNode } from 'react'
import { BrandWordmark } from './Brand'

export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error('InspectPin interface error', error.name, info.componentStack) }
  render() {
    if (this.state.failed) return <main className="fatal-state"><BrandWordmark /><h1>The interface needs a reset.</h1><p>Your device data was not changed. Reload the application to reconnect.</p><button onClick={() => location.reload()}>Reload InspectPin</button></main>
    return this.props.children
  }
}
