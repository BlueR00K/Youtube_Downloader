import React, { useState } from 'react'
import axios from 'axios'

export default function App() {
    const [url, setUrl] = useState('')
    const [info, setInfo] = useState(null)
    const [loading, setLoading] = useState(false)
    const [downloadFormat, setDownloadFormat] = useState(null)

    const fetchInfo = async () => {
        setLoading(true)
        setInfo(null)
        try {
            const res = await axios.post('http://localhost:8000/api/info', { url })
            setInfo(res.data)
        } catch (err) {
            alert('Error fetching info: ' + (err?.response?.data?.detail || err.message))
        } finally {
            setLoading(false)
        }
    }

    const download = async (format_id) => {
        try {
            // Trigger browser download by navigating to blob URL
            const res = await axios.post('http://localhost:8000/api/download', { url, format_id }, {
                responseType: 'blob'
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
                    <h4>{info.title}</h4>
                    <p>Uploader: {info.uploader} • Duration: {info.duration}s</p>

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
                                        <td>{f.format_note}</td>
                                        <td>{f.filesize ? (Math.round(f.filesize / 1024) + ' KB') : '-'}</td>
                                        <td>{f.acodec}</td>
                                        <td>{f.vcodec}</td>
                                        <td><button className="btn btn-sm btn-success" onClick={() => download(f.format_id)}>Download</button></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            <hr />
            <footer className="text-muted small">Note: This is a local development server. For production, secure the API and restrict CORS.</footer>
        </div>
    )
}
