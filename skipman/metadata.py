# ── ID3 Metadata Handler (mutagen) ──────────────────────────────────────────

import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, ID3NoHeaderError


def read_tags(filepath):
    """Read ID3 tags from an MP3 file."""
    try:
        audio = MP3(filepath, ID3=ID3)
        tags = audio.tags
        if tags is None:
            return {"title": "", "artist": "", "album": "", "artwork": None}
        return {
            "title": str(tags.get("TIT2", "")),
            "artist": str(tags.get("TPE1", "")),
            "album": str(tags.get("TALB", "")),
            "artwork": tags.getall("APIC")[0] if tags.getall("APIC") else None,
        }
    except Exception:
        return {"title": "", "artist": "", "album": "", "artwork": None}


def write_tags(filepath, title=None, artist=None, album=None,
               artwork_path=None, artwork_data=None, clear_artwork=False):
    """
    Write ID3 tags to an MP3 file.

    Args:
        filepath: Path to the MP3 file
        title: Song title (TIT2)
        artist: Artist name (TPE1)
        album: Album name (TALB)
        artwork_path: Path to an image file to embed as cover art
        artwork_data: Raw image bytes to embed (alternative to artwork_path)
        clear_artwork: If True, remove all artwork
    """
    try:
        audio = MP3(filepath, ID3=ID3)
    except ID3NoHeaderError:
        audio = MP3(filepath)
        audio.add_tags()

    tags = audio.tags

    if title is not None:
        tags["TIT2"] = TIT2(encoding=3, text=title)
    if artist is not None:
        tags["TPE1"] = TPE1(encoding=3, text=artist)
    if album is not None:
        tags["TALB"] = TALB(encoding=3, text=album)

    if clear_artwork:
        tags.delall("APIC")
    elif artwork_path and os.path.exists(artwork_path):
        ext = os.path.splitext(artwork_path)[1].lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"
        with open(artwork_path, "rb") as f:
            data = f.read()
        tags.delall("APIC")
        tags.add(APIC(
            encoding=3,
            mime=mime,
            type=3,       # Front cover
            desc="Cover",
            data=data,
        ))
    elif artwork_data:
        tags.delall("APIC")
        tags.add(APIC(
            encoding=3,
            mime="image/jpeg",
            type=3,
            desc="Cover",
            data=artwork_data,
        ))

    audio.save()
