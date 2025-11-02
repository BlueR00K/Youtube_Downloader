import os
import tempfile
from typing import Dict, Any
from yt_dlp import YoutubeDL


def get_info(url: str) -> Dict[str, Any]:
    """Return metadata for the given URL without downloading."""
    ydl_opts = {"quiet": True, "skip_download": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info


def download_to_file(url: str, format_id: str | None = None) -> str:
    """Download the requested format to a temporary file and return its path.

    Caller is responsible for deleting the file after use.
    """
    tmpdir = tempfile.mkdtemp(prefix="ytdl_")
    outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")

    ydl_opts: Dict[str, Any] = {
        "outtmpl": outtmpl,
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
    }
    if format_id:
        ydl_opts["format"] = format_id

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

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
