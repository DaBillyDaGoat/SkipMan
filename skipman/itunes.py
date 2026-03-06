# ── iTunes / Apple Music Desktop Integration ────────────────────────────────
# Copies tracks to the "Automatically Add to Apple Music" folder.
# Auto-converts unsupported formats (opus, flac, wav, etc.) to MP3 via ffmpeg.
# Apple Music picks them up automatically and syncs to iCloud Music Library.

import os
import shutil
import subprocess
from pathlib import Path

AUTO_ADD_FOLDER = (
    Path.home() / "Music" / "Apple Music" / "Media"
    / "Automatically Add to Apple Music"
)

# Formats Apple Music accepts natively
NATIVE_FORMATS = {".mp3", ".m4a", ".aac", ".aiff", ".wav", ".alac"}

# Formats that need conversion to MP3
NEEDS_CONVERSION = {".opus", ".ogg", ".wma", ".flac", ".webm"}


def _get_ffmpeg_path():
    """Find ffmpeg executable — check local ffmpeg/ dir first, then PATH."""
    # Check local ffmpeg directory (downloaded by ffmpeg_setup.py)
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_ffmpeg = os.path.join(app_dir, "ffmpeg", "ffmpeg.exe")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg

    # Check system PATH
    if shutil.which("ffmpeg"):
        return "ffmpeg"

    return None


def _convert_to_mp3(input_path, output_path, ffmpeg_path="ffmpeg"):
    """Convert an audio file to 320kbps MP3 using ffmpeg."""
    cmd = [
        ffmpeg_path, "-y", "-i", input_path,
        "-codec:a", "libmp3lame", "-b:a", "320k",
        "-map_metadata", "0",
        output_path,
    ]
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg conversion failed:\n{result.stderr.decode(errors='replace')[:500]}"
        )


def add_to_itunes(file_path):
    """
    Add an audio file to the Apple Music library by copying it
    to the auto-add folder. Converts unsupported formats to MP3 first.

    Args:
        file_path: Absolute path to the audio file

    Returns:
        (True, message) on success

    Raises:
        FileNotFoundError: If the file doesn't exist
        RuntimeError: If the auto-add folder doesn't exist or conversion fails
    """
    file_path = os.path.abspath(file_path)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if not AUTO_ADD_FOLDER.exists():
        raise RuntimeError(
            "Apple Music auto-add folder not found.\n"
            "Make sure Apple Music is installed and has been opened at least once.\n"
            f"Expected: {AUTO_ADD_FOLDER}"
        )

    ext = os.path.splitext(file_path)[1].lower()
    basename = os.path.basename(file_path)

    if ext in NEEDS_CONVERSION:
        # Convert to MP3 first
        ffmpeg_path = _get_ffmpeg_path()
        if not ffmpeg_path:
            raise RuntimeError(
                f'"{basename}" is {ext} format which Apple Music cannot import.\n'
                "FFmpeg is needed to convert it but was not found.\n"
                "Run SkipMan's download feature once to auto-install FFmpeg."
            )

        mp3_name = os.path.splitext(basename)[0] + ".mp3"
        dest = AUTO_ADD_FOLDER / mp3_name

        _convert_to_mp3(file_path, str(dest), ffmpeg_path)
        return True, f'"{basename}" converted to MP3 and added to Apple Music!'

    else:
        # Native format — just copy
        dest = AUTO_ADD_FOLDER / basename
        shutil.copy2(file_path, dest)
        return True, f'"{basename}" added to Apple Music! It will sync to your phone.'
