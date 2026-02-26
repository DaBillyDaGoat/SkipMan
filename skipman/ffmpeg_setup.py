# ── FFmpeg Auto-Setup ───────────────────────────────────────────────────────
# Checks for ffmpeg in PATH, then falls back to bundled imageio-ffmpeg.
# Installs imageio-ffmpeg via pip if nothing is found.

import os
import shutil
import subprocess
import sys


def get_ffmpeg_location():
    """
    Find ffmpeg installation.
    Returns the directory containing ffmpeg.exe, or None if it's in PATH.
    Raises RuntimeError if ffmpeg cannot be found anywhere.
    """
    # 1. Check system PATH
    if shutil.which("ffmpeg"):
        return None  # yt-dlp finds it automatically

    # 2. Check local ./ffmpeg/ directory next to the project
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_dir = os.path.join(app_dir, "ffmpeg")
    local_exe = os.path.join(local_dir, "ffmpeg.exe")
    if os.path.exists(local_exe):
        return local_dir

    # 3. Try imageio-ffmpeg package
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return os.path.dirname(exe)
    except ImportError:
        pass

    return None  # Not found


def ensure_ffmpeg(status_callback=None):
    """
    Ensure ffmpeg is available. Installs imageio-ffmpeg via pip if needed.
    Returns the ffmpeg directory path, or None if in system PATH.
    """
    loc = get_ffmpeg_location()
    if loc is not None:
        return loc

    # Already in PATH?
    if shutil.which("ffmpeg"):
        return None

    # Need to install imageio-ffmpeg
    if status_callback:
        status_callback("FFmpeg not found \u2014 installing (one-time download)...")

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "imageio-ffmpeg"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            "Failed to install FFmpeg automatically.\n"
            "Please install FFmpeg manually: https://ffmpeg.org/download.html"
        ) from e

    # Import the freshly installed package
    import importlib
    imageio_ffmpeg = importlib.import_module("imageio_ffmpeg")
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    if exe and os.path.exists(exe):
        if status_callback:
            status_callback("FFmpeg installed successfully.")
        return os.path.dirname(exe)

    raise RuntimeError(
        "FFmpeg installation succeeded but binary not found.\n"
        "Please install FFmpeg manually: https://ffmpeg.org/download.html"
    )
