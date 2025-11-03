import os
import tempfile
from typing import Dict, Any, Callable, Optional
from yt_dlp import YoutubeDL


def get_info(url: str) -> Dict[str, Any]:
    """Return metadata for the given URL without downloading."""
    ydl_opts = {"quiet": True, "skip_download": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info


def download_to_file(url: str, format_id: str | None = None, progress_hook: Optional[Callable[[dict], None]] = None) -> str:
    """Download the requested format to a temporary file and return its path.

    Caller is responsible for deleting the file after use.
    """
    tmpdir = tempfile.mkdtemp(prefix="ytdl_")
    outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")

    # Add conservative retry options: yt-dlp supports 'retries' and 'fragment_retries'
    # which help for transient network/SSL issues. We also set a socket timeout.
    ydl_opts: Dict[str, Any] = {
        "outtmpl": outtmpl,
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
        "retries": 3,
        "fragment_retries": 3,
        # socket timeout for network operations (seconds)
        "socket_timeout": 30,
    }
    if format_id:
        ydl_opts["format"] = format_id

    # Attach progress hook if provided
    if progress_hook:
        # yt-dlp expects a callable that accepts a status dict
        ydl_opts["progress_hooks"] = [progress_hook]

    # Try a small retry loop around yt-dlp in case of intermittent SSL/network failures
    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            last_exc = None
            break
        except Exception as e:
            last_exc = e
            # for transient network errors, retry a couple of times
            if attempt < 3:
                import time

                time.sleep(1 + attempt * 2)
                continue
            # otherwise re-raise after attempts exhausted
            raise

    # Find downloaded filename from info
    # yt-dlp may return entries or a dict; handle both
    if isinstance(info, dict):
        if "_filename" in info:
            return info["_filename"]
        # if entries exist, get first
        if "entries" in info and info["entries"]:
            e = info["entries"][0]
            if "_filename" in e:
                return e["_filename"]

    # Fallback: pick the most recent file in tmpdir
    files = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir)]
    if not files:
        raise FileNotFoundError("No file was downloaded")
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]
