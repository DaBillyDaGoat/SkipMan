# ── iTunes / Apple Music Desktop Integration ────────────────────────────────
# Uses Windows COM automation to add tracks to the iTunes library.
# With iCloud Music Library / Sync Library enabled, tracks sync to the phone.

import os


def add_to_itunes(mp3_path):
    """
    Add an MP3 file to the iTunes / Apple Music desktop library.

    Args:
        mp3_path: Absolute path to the MP3 file

    Returns:
        (True, message) on success

    Raises:
        FileNotFoundError: If the MP3 file doesn't exist
        RuntimeError: If iTunes isn't installed or COM fails
    """
    mp3_path = os.path.abspath(mp3_path)

    if not os.path.exists(mp3_path):
        raise FileNotFoundError(f"File not found: {mp3_path}")

    try:
        import win32com.client
    except ImportError:
        raise RuntimeError(
            "pywin32 is not installed.\n"
            "Run: pip install pywin32"
        )

    try:
        itunes = win32com.client.Dispatch("iTunes.Application")
    except Exception:
        raise RuntimeError(
            "Could not connect to iTunes.\n"
            "Make sure iTunes / Apple Music is installed on this PC."
        )

    try:
        result = itunes.LibraryPlaylist.AddFile(mp3_path)
        name = os.path.basename(mp3_path)
        return True, f'"{name}" added to iTunes library! It will sync to your phone.'
    except Exception as e:
        raise RuntimeError(f"Failed to add to iTunes: {e}")
