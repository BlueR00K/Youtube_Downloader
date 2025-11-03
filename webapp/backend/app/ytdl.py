import os
import tempfile
import subprocess
from typing import Dict, Any, Callable, Optional
from yt_dlp import YoutubeDL
from yt_dlp.networking._urllib import SSLError as YTDLPSSLError
import requests
import ssl
from urllib.parse import urlparse
import logging
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

# Force TLS 1.2 for all HTTPS requests


class TLS12HttpAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=ssl.PROTOCOL_TLSv1_2,
        )


# Create a session with TLS 1.2 adapter
session = requests.Session()
session.mount("https://", TLS12HttpAdapter())

logger = logging.getLogger("ytdl")


def get_info(url: str) -> Dict[str, Any]:
    """Return metadata for the given URL without downloading."""
    ydl_opts = {"quiet": True, "skip_download": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info


def _aria2_available() -> bool:
    from shutil import which

    return which("aria2c") is not None


def _aria2_download(url: str, out_path: str) -> bool:
    """Try to download using aria2c if available. Returns True on success."""
    if not _aria2_available():
        return False
    try:
        # -x 4 = 4 connections, -s 4 splits
        subprocess.run(["aria2c", "-x", "4", "-s", "4", "-o", os.path.basename(
            out_path), url], cwd=os.path.dirname(out_path), check=True)
        return os.path.exists(out_path)
    except Exception:
        logger.exception("aria2c download failed")
        return False


def download_to_file(url: str, format_id: Optional[str] = None, progress_hook: Optional[Callable[[dict], None]] = None, output_dir: Optional[str] = None) -> str:
    """Download the requested format and save it to a specified directory or temporary directory.

    Args:
        url: URL to download from
        format_id: Optional format/quality selection
        progress_hook: Optional callback for progress updates
        output_dir: Optional directory to save files to. If None, uses a temp dir.

    Returns:
        Path to the downloaded file
    """
    if output_dir:
        # Ensure output dir exists
        os.makedirs(output_dir, exist_ok=True)
        # Use output_dir but keep random prefix for uniqueness
        prefix = f"ytdl_{os.urandom(4).hex()}_"
        tmpdir = output_dir
        outtmpl = os.path.join(output_dir, prefix + "%(title)s.%(ext)s")
    else:
        # Default temp dir behavior
        tmpdir = tempfile.mkdtemp(prefix="ytdl_")
        outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")

    # yt-dlp options
    ydl_opts: Dict[str, Any] = {
        "outtmpl": outtmpl,
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
        "prefer_insecure": True,  # Allow fallback to HTTP if HTTPS fails
        "http_headers": {  # Add common headers
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    # Try to use system downloaders if available for native TLS handling
    from shutil import which
    if which("aria2c"):
        ydl_opts["external_downloader"] = "aria2c"
        ydl_opts["external_downloader_args"] = [
            "aria2c:--min-tls-version=TLSv1.2", "-x", "4", "-k", "1M"]
    elif which("curl"):
        ydl_opts["external_downloader"] = "curl"
        ydl_opts["external_downloader_args"] = ["--tlsv1.2", "-L"]
    if format_id:
        ydl_opts["format"] = format_id

    # Fast-path: if the URL looks like a direct media resource, try requests first.
    try:
        head = session.head(url, allow_redirects=True, timeout=10)
        ctype = head.headers.get("content-type", "")
        ctype = ctype.lower() if isinstance(ctype, str) else ""
        if ctype.startswith("image/") or ctype.startswith("video/") or ctype.startswith("audio/"):
            ext = ""
            if "/" in ctype:
                parts = ctype.split("/", 1)[1]
                subtype = parts.split(";", 1)[0].strip()
                if subtype:
                    ext = "." + subtype
            out_path = os.path.join(tmpdir, "download" + ext)
            try:
                r = session.get(url, stream=True, timeout=30)
                r.raise_for_status()
            except requests.exceptions.SSLError:
                logger.warning(
                    "requests SSL error for %s, trying alternate TLS version", url)
                try:
                    # Try TLS 1.1 if 1.2 fails
                    class TLS11HttpAdapter(HTTPAdapter):
                        def init_poolmanager(self, connections, maxsize, block=False):
                            self.poolmanager = PoolManager(
                                num_pools=connections, maxsize=maxsize, block=block, ssl_version=ssl.PROTOCOL_TLSv1_1)
                    alt_session = requests.Session()
                    alt_session.mount("https://", TLS11HttpAdapter())
                    r = alt_session.get(url, stream=True, timeout=30)
                    r.raise_for_status()
                except requests.exceptions.SSLError:
                    logger.warning(
                        "TLS 1.1 failed for %s, retrying insecurely as last resort", url)
                    r = requests.get(url, stream=True,
                                     timeout=30, verify=False)
                    r.raise_for_status()
            with open(out_path, "wb") as wf:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        wf.write(chunk)
            return out_path
    except Exception:
        # ignore and let yt-dlp try
        pass

    # Attach progress hook if provided
    if progress_hook:
        ydl_opts["progress_hooks"] = [progress_hook]

    # Try a small retry loop around yt-dlp
    last_exc: Optional[Exception] = None
    info = None
    for attempt in range(1, 4):
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            last_exc = None
            break
        except Exception as e:
            last_exc = e
            if attempt < 3:
                import time

                time.sleep(1 + attempt * 2)
                continue

            # exhausted attempts: if caused by SSL EOF and URL is direct-file, try fallbacks
            try:
                cause = getattr(e, "__cause__", None)
                is_ssl = isinstance(
                    cause, YTDLPSSLError) or "UNEXPECTED_EOF_WHILE_READING" in str(e)
            except Exception:
                is_ssl = False

            parsed = urlparse(url)
            path = parsed.path or ""
            ext = os.path.splitext(path)[1].lower()
            direct_exts = {".png", ".jpg", ".jpeg", ".gif",
                           ".webp", ".mp4", ".mp3", ".wav", ".m4a"}
            if is_ssl and ext in direct_exts:
                out_path = os.path.join(tmpdir, "download" + ext)
                # Try aria2 if present
                if _aria2_available():
                    ok = _aria2_download(url, out_path)
                    if ok:
                        return out_path
                # Try to force yt-dlp to use an external downloader (curl/wget) which
                # uses the system TLS stack instead of Python's. This can avoid
                # environment-specific SSL EOF failures.
                from shutil import which

                def _try_with_external(name: str, args: list[str]) -> Optional[str]:
                    if which(name) is None:
                        return None
                    opts = dict(ydl_opts)
                    opts.update({
                        "external_downloader": name,
                        "external_downloader_args": args,
                    })
                    try:
                        with YoutubeDL(opts) as ydl2:
                            info2 = ydl2.extract_info(url, download=True)
                        # try to resolve filename from info2
                        if isinstance(info2, dict):
                            if "_filename" in info2:
                                return info2["_filename"]
                            if "entries" in info2 and info2["entries"]:
                                e2 = info2["entries"][0]
                                if "_filename" in e2:
                                    return e2["_filename"]
                    except Exception:
                        logger.exception("external downloader %s failed", name)
                    return None

                # try curl then wget
                try:
                    fname = _try_with_external(
                        "curl", ["-L"]) or _try_with_external("wget", ["-c"])
                    if fname:
                        return fname
                except Exception:
                    # fall through to requests fallback
                    pass
                # Try requests (first verified, then insecure if SSL fails)
                try:
                    resp = requests.get(url, stream=True, timeout=30)
                    resp.raise_for_status()
                except requests.exceptions.SSLError:
                    logger.warning(
                        "requests SSL error on fallback for %s, retrying insecurely", url)
                    resp = requests.get(
                        url, stream=True, timeout=30, verify=False)
                    resp.raise_for_status()
                with open(out_path, "wb") as wf:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            wf.write(chunk)
                return out_path

            # re-raise original exception if no fallback
            raise

    # If yt-dlp returned info, try to find the filename
    if isinstance(info, dict):
        if "_filename" in info:
            return info["_filename"]
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
