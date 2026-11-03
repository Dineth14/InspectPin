import { useEffect, useState } from 'react'
import { ApiClient } from '../api'
import { Skeleton } from './Ui'

export function AuthenticatedImage({ api, mediaId, alt, className = '' }: { api: ApiClient; mediaId?: string; alt: string; className?: string }) {
  const [url, setUrl] = useState(''), [failed, setFailed] = useState(false)
  useEffect(() => {
    let live = true, objectUrl = ''
    setUrl(''); setFailed(false)
    if (!mediaId) return
    api.mediaObjectUrl(mediaId).then(value => { objectUrl = value; if (live) setUrl(value); else URL.revokeObjectURL(value) }).catch(() => { if (live) setFailed(true) })
    return () => { live = false; if (objectUrl) URL.revokeObjectURL(objectUrl) }
  }, [api, mediaId])
  if (!mediaId || failed) return <div className={`media-fallback ${className}`} role="img" aria-label={`${alt}; image unavailable`}><span>Evidence unavailable</span></div>
  if (!url) return <Skeleton className={`media-skeleton ${className}`} />
  return <img className={className} src={url} alt={alt} loading="lazy" />
}
