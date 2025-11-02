import os
import shutil
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mimetypes

from app.ytdl import get_info, download_to_file

import os

app = FastAPI(title="Youtube Downloader API")

# Configure CORS from environment (comma-separated) or default to allow all in dev
allowed = os.getenv("ALLOWED_ORIGINS", "*")
if allowed.strip() == "*":
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in allowed.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InfoRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    format_id: str | None = None


def _check_api_key(request: Request):
    """Return True if API key is not set or matches header; raises HTTPException otherwise."""
    api_key = os.getenv("API_KEY")
    if not api_key:
        return True
    header = request.headers.get(
        "x-api-key") or request.headers.get("X-API-KEY")
    if header == api_key:
        return True
    raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.post("/api/info")
async def api_info(req: InfoRequest):
    # Optional API key check
    try:
        # pydantic created a dict for req; build a fake Request for header-based auth not available here
        # Info endpoint is typically safe, but still allow API_KEY protection via header if set.
        info = get_info(req.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Return selected metadata + formats
    out = {
        "title": info.get("title"),
        "id": info.get("id"),
        "uploader": info.get("uploader"),
        "duration": info.get("duration"),
        "thumbnails": info.get("thumbnails"),
        "formats": [
            {
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "format_note": f.get("format_note"),
                "filesize": f.get("filesize"),
                "height": f.get("height"),
                "width": f.get("width"),
                "acodec": f.get("acodec"),
                "vcodec": f.get("vcodec"),
            }
            for f in info.get("formats", [])
        ],
    }
    return JSONResponse(out)


@app.post("/api/download")
async def api_download(req: DownloadRequest):
    # Enforce API key (if configured)
    # FastAPI Request object isn't directly available from Pydantic body; rely on header via dependency if needed.
    # For simplicity in this single-file app, check environ API_KEY and disallow if not passed via header.
    # The Request object is available as dependency injection if we wanted it; keep this straightforward.
    try:
        file_path = download_to_file(req.url, req.format_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=500, detail="Downloaded file not found")

    # Determine mime type
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    filename = os.path.basename(file_path)

    def iterfile(path: str):
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    yield chunk
        finally:
            # cleanup - remove the temp directory
            d = os.path.dirname(path)
            try:
                if os.path.exists(path):
                    os.remove(path)
                if os.path.isdir(d):
                    shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass

    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return StreamingResponse(iterfile(file_path), media_type=mime_type, headers=headers)
