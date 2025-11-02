import React, { useState } from 'react'
import axios from 'axios'

const BACKEND = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001'

function humanFileSize(bytes) {
  if (!bytes) return '-'
  const thresh = 1024
  if (Math.abs(bytes) < thresh) return bytes + ' B'
  const units = ['KB', 'MB', 'GB', 'TB']
  let u = -1
  do {
    bytes /= thresh
    ++u
  } while (Math.abs(bytes) >= thresh && u < units.length - 1)
  return bytes.toFixed(1) + ' ' + units[u]
}

export default function App() {
  const [singleUrl, setSingleUrl] = useState('')
  const [multiUrls, setMultiUrls] = useState('')
  const [info, setInfo] = useState(null)
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [progress, setProgress] = useState(0)

  const fetchInfo = async () => {
    setLoading(true)
    setInfo(null)
    try {
      const urls = multiUrls.split('\n').map(s => s.trim()).filter(Boolean)
      if (urls.length > 1) {
        const res = await axios.post(`${BACKEND}/api/infos`, { urls })
        setInfo({ batch: true, items: res.data })
      } else {
        const value = urls[0] || singleUrl
        const res = await axios.post(`${BACKEND}/api/info`, { url: value })
        setInfo({ batch: false, item: res.data, url: value })
      }
    } catch (err) {
      alert('Error fetching info: ' + (err?.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  const downloadSingle = async (targetUrl, format_id) => {
    try {
      setDownloading(true)
      setProgress(0)
      const res = await axios.post(`${BACKEND}/api/download`, { url: targetUrl, format_id }, {
        responseType: 'blob',
        onDownloadProgress: (evt) => {
          if (evt.lengthComputable) setProgress(Math.round((evt.loaded / evt.total) * 100))
        }
      })
      const disposition = res.headers['content-disposition'] || ''
      let filename = 'download'
      const m = /filename="?([^";]+)"?/.exec(disposition)
      if (m) filename = m[1]
      const blob = new Blob([res.data])
      const link = document.createElement('a')
      link.href = window.URL.createObjectURL(blob)
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      alert('Download failed: ' + (err?.response?.data?.detail || err.message))
    } finally {
      setDownloading(false)
      setProgress(0)
    }
  }

  const downloadAll = async () => {
    try {
      setDownloading(true)
      setProgress(0)
      const urls = multiUrls.split('\n').map(s => s.trim()).filter(Boolean)
      if (urls.length === 0 && singleUrl) urls.push(singleUrl)
      if (urls.length === 0) {
        alert('No URLs provided')
        return
      }
      const res = await axios.post(`${BACKEND}/api/downloads`, { urls }, { responseType: 'blob', onDownloadProgress: (evt) => { if (evt.lengthComputable) setProgress(Math.round((evt.loaded / evt.total) * 100)) } })
      const disposition = res.headers['content-disposition'] || ''
      let filename = 'downloads.zip'
      const m = /filename="?([^";]+)"?/.exec(disposition)
      if (m) filename = m[1]
      const blob = new Blob([res.data])
      const link = document.createElement('a')
      link.href = window.URL.createObjectURL(blob)
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      alert('Batch download failed: ' + (err?.response?.data?.detail || err.message))
    } finally {
      setDownloading(false)
      setProgress(0)
    }
  }

  return (
    <div className="container py-4">
      <h1 className="mb-4">YouTube Downloader</h1>

      <div className="mb-3">
        <label className="form-label">Single URL (optional)</label>
        <input className="form-control" value={singleUrl} onChange={(e) => setSingleUrl(e.target.value)} placeholder="https://..." />
      </div>

      <div className="mb-3">
        <label className="form-label">Or paste multiple URLs (one per line)</label>
        <textarea className="form-control" rows={4} value={multiUrls} onChange={(e) => setMultiUrls(e.target.value)} placeholder="https://..." />
      </div>

      <div className="mb-3">
        <button className="btn btn-primary me-2" onClick={fetchInfo} disabled={loading || (!singleUrl && !multiUrls)}>Get Info</button>
        <button className="btn btn-secondary" onClick={downloadAll} disabled={downloading || (!singleUrl && !multiUrls)}>Download All (ZIP)</button>
      </div>

      {loading && <div className="alert alert-info">Loading...</div>}

      {info && info.batch && (
        <div>
          <h4>Batch results</h4>
          {info.items.map((it, idx) => (
            <div key={idx} className="card mb-3">
              <div className="card-body">
                <div className="d-flex gap-3 align-items-start mb-2">
                  {it.thumbnails && it.thumbnails.length > 0 && (<img src={it.thumbnails[it.thumbnails.length-1].url} alt="thumb" style={{maxWidth:160}} />)}
                  <div>
                    <strong>{it.title || it.url}</strong>
                    <div className="text-muted small">{it.uploader || ''}  {it.duration ? `${it.duration}s` : ''}</div>
                    {it.error && <div className="text-danger">Error: {it.error}</div>}
                  </div>
                </div>
                {it.formats && (
                  <div className="table-responsive">
                    <table className="table table-sm">
                      <thead><tr><th>Format</th><th>Ext</th><th>Size</th><th></th></tr></thead>
                      <tbody>
                        {it.formats.map(f => (
                          <tr key={f.format_id}>
                            <td>{f.format_id}</td>
                            <td>{f.ext}</td>
                            <td>{humanFileSize(f.filesize)}</td>
                            <td><button className="btn btn-sm btn-success" onClick={() => downloadSingle(it.url, f.format_id)} disabled={downloading}>{downloading ? 'Downloading...' : 'Download'}</button></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {info && !info.batch && (
        <div>
          <div className="d-flex gap-3 align-items-start mb-3">
            {info.item.thumbnails && info.item.thumbnails.length > 0 && (<img src={info.item.thumbnails[info.item.thumbnails.length-1].url} alt="thumb" style={{maxWidth:220}} />)}
            <div>
              <h4 className="mb-1">{info.item.title}</h4>
              <p className="mb-1">Uploader: {info.item.uploader}  Duration: {info.item.duration}s</p>
              <p className="text-muted small mb-0">ID: {info.item.id}</p>
            </div>
          </div>
          <div className="table-responsive">
            <table className="table table-sm table-hover">
              <thead><tr><th>Format ID</th><th>Ext</th><th>Note</th><th>Size</th><th></th></tr></thead>
              <tbody>
                {info.item.formats.map(f => (
                  <tr key={f.format_id}>
                    <td>{f.format_id}</td>
                    <td>{f.ext}</td>
                    <td style={{maxWidth:200}}>{f.format_note}</td>
                    <td>{humanFileSize(f.filesize)}</td>
                    <td><button className="btn btn-sm btn-success" onClick={() => downloadSingle(info.url || singleUrl, f.format_id)} disabled={downloading}>{downloading ? 'Downloading...' : 'Download'}</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {downloading && (
        <div className="mt-3">
          <div className="progress">
            <div className="progress-bar" role="progressbar" style={{width: `${progress}%`}} aria-valuenow={progress} aria-valuemin="0" aria-valuemax="100">{progress}%</div>
          </div>
        </div>
      )}

      <hr />
      <footer className="text-muted small">Note: This is a local development server. For production, secure the API and restrict CORS.</footer>
    </div>
  )
}
