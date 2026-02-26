# ── yt-dlp Download Wrapper ─────────────────────────────────────────────────

import os
import re


APPLE_MUSIC_PATTERN = re.compile(r"(music\.apple\.com|itunes\.apple\.com)", re.I)


def detect_apple_music(url):
    """Check if URL is an Apple Music / iTunes link (DRM-protected)."""
    return bool(APPLE_MUSIC_PATTERN.search(url))


def download_song(url, save_dir, progress_callback=None, ffmpeg_location=None):
    """
    Download audio from URL and convert to MP3.

    Args:
        url: YouTube / SoundCloud / etc. URL
        save_dir: Directory to save the MP3
        progress_callback: yt-dlp progress hook function
        ffmpeg_location: Path to directory containing ffmpeg.exe (or None for PATH)

    Returns:
        dict with keys: title, artist, album, thumbnail_url, file_path

    Raises:
        ValueError: If the URL is from Apple Music (DRM-protected)
        Exception: On download failure
    """
    if detect_apple_music(url):
        raise ValueError(
            "Apple Music links are DRM-protected and cannot be downloaded.\n"
            "Paste a YouTube or SoundCloud link instead."
        )

    import yt_dlp

    os.makedirs(save_dir, exist_ok=True)

    outtmpl = os.path.join(save_dir, "%(title)s.%(ext)s")

    opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }],
        "quiet": True,
        "no_warnings": True,
    }

    if ffmpeg_location:
        opts["ffmpeg_location"] = ffmpeg_location

    if progress_callback:
        opts["progress_hooks"] = [progress_callback]

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

        # Get the actual output filename (sanitized by yt-dlp)
        prepared = ydl.prepare_filename(info)
        mp3_path = os.path.splitext(prepared)[0] + ".mp3"

    title = info.get("title") or "Unknown"
    artist = info.get("artist") or info.get("creator") or info.get("uploader") or ""
    album = info.get("album") or ""
    thumbnail = info.get("thumbnail") or ""

    # Fallback: if the expected path doesn't exist, search for latest .mp3
    if not os.path.exists(mp3_path):
        mp3_files = [
            os.path.join(save_dir, f)
            for f in os.listdir(save_dir)
            if f.lower().endswith(".mp3")
        ]
        if mp3_files:
            mp3_path = max(mp3_files, key=os.path.getmtime)

    return {
        "title": title,
        "artist": artist,
        "album": album,
        "thumbnail_url": thumbnail,
        "file_path": mp3_path,
    }
