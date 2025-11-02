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
    const [url, setUrl] = useState('')
    const [info, setInfo] = useState(null)
    const [loading, setLoading] = useState(false)
    const [downloading, setDownloading] = useState(false)
    const [progress, setProgress] = useState(0)

    const fetchInfo = async () => {
        setLoading(true)
        setInfo(null)
        try {
            const res = await axios.post(`${BACKEND}/api/info`, { url })
            setInfo(res.data)
        } catch (err) {
            alert('Error fetching info: ' + (err?.response?.data?.detail || err.message))
        } finally {
            setLoading(false)
        }
    }

    const download = async (format_id) => {
        try {
            setDownloading(true)
            setProgress(0)
            const res = await axios.post(`${BACKEND}/api/download`, { url, format_id }, {
                responseType: 'blob',
                onDownloadProgress: (evt) => {
                    if (evt.lengthComputable) {
                        setProgress(Math.round((evt.loaded / evt.total) * 100))
                    }
                }
            })

            const disposition = res.headers['content-disposition'] || ''
            let filename = 'download'
            const m = /filename=\"?([^\";]+)\"?/.exec(disposition)
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

    return (
        <div className="container py-4">
            <h1 className="mb-4">YouTube Downloader</h1>

            <div className="mb-3">
                <label className="form-label">YouTube / URL</label>
                <input className="form-control" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://www.youtube.com/watch?v=..." />
            </div>

            <div className="mb-3">
                <button className="btn btn-primary me-2" onClick={fetchInfo} disabled={loading || !url}>Get Info</button>
            </div>

            {loading && <div className="alert alert-info">Loading...</div>}

            {info && (
                <div>
                    <div className="d-flex gap-3 align-items-start mb-3">
                        {info.thumbnails && info.thumbnails.length > 0 && (
                            <img src={info.thumbnails[info.thumbnails.length - 1].url} alt="thumbnail" style={{ maxWidth: 220, borderRadius: 8 }} />
                        )}
                        <div>
                            <h4 className="mb-1">{info.title}</h4>
                            <p className="mb-1">Uploader: {info.uploader} • Duration: {info.duration}s</p>
                            <p className="text-muted small mb-0">ID: {info.id}</p>
                        </div>
                    </div>

                    <h5>Formats</h5>
                    <div className="table-responsive">
                        <table className="table table-sm table-hover">
                            <thead>
                                <tr>
                                    <th>Format ID</th>
                                    <th>Ext</th>
                                    <th>Note</th>
                                    <th>Size</th>
                                    <th>Audio</th>
                                    <th>Video</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {info.formats.map((f) => (
                                    <tr key={f.format_id}>
                                        <td>{f.format_id}</td>
                                        <td>{f.ext}</td>
                                        <td style={{ maxWidth: 200 }}>{f.format_note}</td>
                                        <td>{humanFileSize(f.filesize)}</td>
                                        <td>{f.acodec}</td>
                                        <td>{f.vcodec}</td>
                                        <td>
                                            <button className="btn btn-sm btn-success" onClick={() => download(f.format_id)} disabled={downloading}>
                                                {downloading ? 'Downloading...' : 'Download'}
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {downloading && (
                        <div className="mt-3">
                            <div className="progress">
                                <div className="progress-bar" role="progressbar" style={{ width: `${progress}%` }} aria-valuenow={progress} aria-valuemin="0" aria-valuemax="100">{progress}%</div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            <hr />
            <footer className="text-muted small">Note: This is a local development server. For production, secure the API and restrict CORS.</footer>
        </div>
    )
}
