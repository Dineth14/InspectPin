import { useEffect, useState } from 'react'
import { ApiClient } from '../api'

export function Recording({api,id,video,seconds}: {api:ApiClient; id:string; video:boolean; seconds?:number}) {
  const [url,setUrl] = useState(''), [error,setError] = useState('')
  const [show,setShow] = useState(false)
  const [preview,setPreview] = useState(false)
  useEffect(() => {
    let active = true, blob = ''
    setUrl(''); setError('')
    const controller = new AbortController()
    if (show) api.mediaObjectUrl(video ? id + (preview ? '/preview' : '/playback') : id, controller.signal)
      .then(value => { blob=value; if (active) setUrl(value); else URL.revokeObjectURL(value) })
      .catch(() => { if (active) setError('Playback unavailable') })
    return () => { active=false; controller.abort(); if(blob) URL.revokeObjectURL(blob) }
  },[api,id,video,show,preview])
  async function download() {
    try {
      const source=await api.mediaObjectUrl(id)
      const link=document.createElement('a')
      link.href=source; link.download=id+(video?'.avi':'.wav'); link.click()
      setTimeout(() => URL.revokeObjectURL(source),30000)
    } catch { setError('Download failed') }
  }
  return <section className="panel"><h2>{video?'Silent video':'Audio observation'}</h2>
    {typeof seconds === 'number' && <p>{seconds.toFixed(1)} s playback</p>}
    <button className="button secondary" onClick={()=>setShow(!show)}>{show?'Close':'Open'} player</button>
    <button className="button secondary" onClick={download}>Download original</button>
    {video && show && <button className="button secondary" onClick={()=>setPreview(!preview)}>{preview?'Use MP4 player':'Use animated preview'}</button>}
    {show && !url && !error && <p role="status">{video && !preview ? 'Preparing silent video…' : 'Loading recording…'}</p>}
    {url && (video?(preview?<img src={url} alt="Animated silent preview"/>:<video src={url} controls playsInline style={{maxWidth:'100%'}}/>):<audio src={url} controls/>)}
    {error && <p role="alert">{error}</p>}</section>
}
