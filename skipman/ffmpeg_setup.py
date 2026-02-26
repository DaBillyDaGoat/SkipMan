# ── FFmpeg Auto-Setup ───────────────────────────────────────────────────────
# Downloads the full FFmpeg (ffmpeg + ffprobe) from GitHub if not found.

import os
import shutil
import subprocess
import sys
import zipfile
import io

# Where we store the local ffmpeg binaries
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG_DIR = os.path.join(APP_DIR, "ffmpeg")

# BtbN builds on GitHub — includes ffmpeg.exe + ffprobe.exe
FFMPEG_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-master-latest-win64-gpl.zip"
)


def get_ffmpeg_location():
    """
    Find ffmpeg + ffprobe installation.
    Returns the directory containing both executables, or None if in PATH.
    """
    # 1. Both in system PATH
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return None

    # 2. Local ./ffmpeg/ directory
    ffmpeg_exe = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
    ffprobe_exe = os.path.join(FFMPEG_DIR, "ffprobe.exe")
    if os.path.exists(ffmpeg_exe) and os.path.exists(ffprobe_exe):
        return FFMPEG_DIR

    return None  # Not found


def ensure_ffmpeg(status_callback=None):
    """
    Ensure ffmpeg + ffprobe are available.
    Downloads from GitHub if not found (one-time ~130MB download).
    Returns the directory path, or None if in system PATH.
    """
    loc = get_ffmpeg_location()
    if loc is not None:
        return loc
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return None

    # Download full FFmpeg build
    if status_callback:
        status_callback("FFmpeg not found — downloading (one-time, ~130MB)...")

    import requests

    try:
        resp = requests.get(FFMPEG_URL, stream=True, timeout=300)
        resp.raise_for_status()

        # Read full content with progress
        total = int(resp.headers.get("content-length", 0))
        data = bytearray()
        downloaded = 0
        for chunk in resp.iter_content(chunk_size=1024 * 256):
            data.extend(chunk)
            downloaded += len(chunk)
            if status_callback and total:
                pct = int(downloaded / total * 100)
                mb = downloaded / (1024 * 1024)
                status_callback(f"Downloading FFmpeg... {mb:.0f}MB ({pct}%)")

        if status_callback:
            status_callback("Extracting FFmpeg...")

        # Extract just the bin/ contents (ffmpeg.exe, ffprobe.exe)
        os.makedirs(FFMPEG_DIR, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(bytes(data))) as zf:
            for member in zf.namelist():
                basename = os.path.basename(member)
                if basename in ("ffmpeg.exe", "ffprobe.exe"):
                    # Extract to flat FFMPEG_DIR
                    target = os.path.join(FFMPEG_DIR, basename)
                    with zf.open(member) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)

        # Verify
        if (os.path.exists(os.path.join(FFMPEG_DIR, "ffmpeg.exe")) and
                os.path.exists(os.path.join(FFMPEG_DIR, "ffprobe.exe"))):
            if status_callback:
                status_callback("FFmpeg ready.")
            return FFMPEG_DIR

        raise RuntimeError("Extraction failed — ffmpeg.exe or ffprobe.exe missing.")

    except requests.RequestException as e:
        raise RuntimeError(
            f"Failed to download FFmpeg: {e}\n"
            "Install manually: https://ffmpeg.org/download.html\n"
            "Put ffmpeg.exe and ffprobe.exe in the 'ffmpeg' folder next to main.py"
        )
