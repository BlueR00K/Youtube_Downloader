# Backend (FastAPI)

This directory contains the FastAPI backend for the Youtube Downloader web app.

Requirements

- Python 3.9+
- Install dependencies:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

Run dev server:

```powershell
# from webapp/backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Notes

- Uses `yt-dlp` to fetch metadata and download files. Downloads are stored in temporary directories and streamed to the client, then cleaned up.
- CORS is enabled for development. Restrict origins for production.
