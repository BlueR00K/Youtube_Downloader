import os
import shutil
import tempfile
import zipfile
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mimetypes

from app.ytdl import get_info, download_to_file
from app.ratelimit import rate_limiter
from fastapi import Depends
from fastapi.security import APIKeyHeader
import os

import logging
import re

app = FastAPI(title="Youtube Downloader API")
logger = logging.getLogger("ytdl")
if not logger.handlers:
    # ensure logs are written to a file for realtime inspection
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        log_dir = None
    log_path = os.path.join(log_dir, 'backend.log') if log_dir else None
    handlers = []
    if log_path:
        handlers.append(logging.FileHandler(log_path))
    handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        handlers=handlers,
    )
    logger = logging.getLogger("ytdl")


def _clean_exc_msg(e: Exception) -> str:
    """Return a cleaned, single-line error message without ANSI color sequences."""
    s = str(e)
    # strip common ANSI escape sequences (colors) and newlines
    s = re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", s)
    s = s.replace("\n", " ")
    return s.strip()


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


class InfoListRequest(BaseModel):
    urls: list[str]


class BatchDownloadRequest(BaseModel):
    # Either provide `items` with url+optional format, or `urls` where format_id applies to all
    items: list[DownloadRequest] | None = None
    urls: list[str] | None = None


# Dependency: enforce API key (if set) and rate limiting per client
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def auth_and_rate_limit(request: Request, api_key: str | None = Depends(api_key_header)):
    """Check API key if configured, then apply a simple rate limit per key or client IP."""
    configured = os.getenv("API_KEY")
    # verify API key if configured
    if configured:
        if not api_key or api_key != configured:
            raise HTTPException(
                status_code=401, detail="Invalid or missing API key")

    # choose rate-limit key: API key if present, else client IP
    key = api_key if api_key else (
        request.client.host if request.client else "unknown")
    rate_limiter.check(key)


@app.post("/api/info")
async def api_info(req: InfoRequest, _=Depends(auth_and_rate_limit)):
    # Optional API key check
    try:
        # pydantic created a dict for req; build a fake Request for header-based auth not available here
        # Info endpoint is typically safe, but still allow API_KEY protection via header if set.
        info = get_info(req.url)
    except Exception as e:
        logger.exception("Error in api_info")
        raise HTTPException(status_code=400, detail=_clean_exc_msg(e))

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


@app.post("/api/infos")
async def api_infos(req: InfoListRequest, _=Depends(auth_and_rate_limit)):
    results = []
    for url in req.urls:
        try:
            info = get_info(url)
            out = {
                "url": url,
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
        except Exception as e:
            logger.exception("Error fetching info for %s", url)
            out = {"url": url, "error": _clean_exc_msg(e)}
        results.append(out)
    return JSONResponse(results)


@app.post("/api/download")
async def api_download(req: DownloadRequest, _=Depends(auth_and_rate_limit)):
    # Enforce API key (if configured)
    # FastAPI Request object isn't directly available from Pydantic body; rely on header via dependency if needed.
    # For simplicity in this single-file app, check environ API_KEY and disallow if not passed via header.
    # The Request object is available as dependency injection if we wanted it; keep this straightforward.
    try:
        file_path = download_to_file(req.url, req.format_id)
    except Exception as e:
        logger.exception("Error in api_download for %s", req.url)
        raise HTTPException(status_code=500, detail=_clean_exc_msg(e))

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=500, detail="Downloaded file not found")

    # determine file size and include Content-Length when available to help client progress
    try:
        file_size = os.path.getsize(file_path)
    except Exception:
        file_size = None

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
    if file_size is not None:
        headers["Content-Length"] = str(file_size)
    return StreamingResponse(iterfile(file_path), media_type=mime_type, headers=headers)


@app.post("/api/downloads")
async def api_downloads(req: BatchDownloadRequest, _=Depends(auth_and_rate_limit)):
    # Build normalized list of DownloadRequest items
    items: list[DownloadRequest] = []
    if req.items:
        items = req.items
    elif req.urls:
        items = [DownloadRequest(url=u) for u in req.urls]
    else:
        raise HTTPException(status_code=400, detail="No urls/items provided")

    # Prepare a temp workspace for the zip
    workspace = tempfile.mkdtemp(prefix="ytdl_batch_")
    downloaded_paths = []
    try:
        # Download each file (blocking call to download_to_file)
        for it in items:
            try:
                p = download_to_file(it.url, it.format_id)
            except Exception as e:
                logger.exception("Batch download error for %s", it.url)
                # record failures as simple text files so user knows
                err_path = os.path.join(
                    workspace, f"error_{len(downloaded_paths)}.txt")
                with open(err_path, "w", encoding="utf-8") as ef:
                    ef.write(
                        f"Failed to download {it.url}: {_clean_exc_msg(e)}\n")
                downloaded_paths.append(err_path)
                continue

            # copy the file into our workspace (download_to_file may create its own temp dir)
            try:
                target = os.path.join(workspace, os.path.basename(p))
                shutil.copy(p, target)
                downloaded_paths.append(target)
            except Exception:
                # if copy fails, still try to include original
                downloaded_paths.append(p)

        # Create a zip archive containing all files
        zip_path = os.path.join(workspace, "downloads.zip")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in downloaded_paths:
                # ensure file exists
                if os.path.exists(path):
                    zf.write(path, arcname=os.path.basename(path))

        # Stream the zip file and cleanup afterwards
        def iterzip(p: str):
            try:
                with open(p, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        yield chunk
            finally:
                # cleanup workspace and any leftover temp dirs
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass
                try:
                    shutil.rmtree(workspace, ignore_errors=True)
                except Exception:
                    pass

        headers = {"Content-Disposition": "attachment; filename=downloads.zip"}
        try:
            zsize = os.path.getsize(zip_path)
        except Exception:
            zsize = None
        if zsize is not None:
            headers["Content-Length"] = str(zsize)
        return StreamingResponse(iterzip(zip_path), media_type="application/zip", headers=headers)
    except Exception as e:
        logger.exception("Unexpected error in api_downloads")
        # ensure workspace is removed on unexpected errors
        try:
            shutil.rmtree(workspace, ignore_errors=True)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=_clean_exc_msg(e))
