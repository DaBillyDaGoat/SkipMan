# ── SkipMan — Main Application Window ───────────────────────────────────────

import tkinter as tk
import os
import sys
import subprocess
import threading

from skipman import theme


# ── Dependencies that auto-install on first run ────────────────────────────
REQUIRED_PACKAGES = {
    "yt_dlp": "yt-dlp",
    "mutagen": "mutagen",
    "PIL": "Pillow",
    "requests": "requests",
}


def _check_and_install_deps(status_callback=None):
    """Check for required packages and pip-install any that are missing."""
    missing = []
    for module_name, pip_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)

    if not missing:
        return

    if status_callback:
        status_callback(f"Installing: {', '.join(missing)}...")

    for pkg in missing:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError:
            if status_callback:
                status_callback(f"Failed to install {pkg}. Run: pip install {pkg}")

    if status_callback:
        status_callback("Dependencies installed.")


class SkipManApp(tk.Tk):
    """Main application window. Manages screen switching and queue state."""

    def __init__(self):
        super().__init__()

        self.title("SkipMan v1.0")
        self.geometry("700x620")
        self.minsize(640, 560)
        self.configure(bg=theme.BG_DARK)

        # Try to set the window icon (won't crash if it fails)
        try:
            self.iconbitmap(default="")
        except tk.TclError:
            pass

        # ── State ───────────────────────────────────────────────────────────
        self.queue = []         # List of URL strings
        self.current_song = None
        self.save_dir = os.path.join(
            os.path.expanduser("~"), "Music", "SkipMan")

        # ── Container ───────────────────────────────────────────────────────
        self.container = tk.Frame(self, bg=theme.BG_DARK)
        self.container.pack(fill="both", expand=True)

        # ── Screens (lazy import to avoid circular) ─────────────────────────
        from skipman.download_screen import DownloadScreen
        from skipman.edit_screen import EditScreen

        self.download_screen = DownloadScreen(self.container, self)
        self.edit_screen = EditScreen(self.container, self)

        self.show_download_screen()

        # ── Startup checks ──────────────────────────────────────────────────
        self._startup_checks()

    def _startup_checks(self):
        """Run dependency checks + FFmpeg check in a background thread."""
        def _check():
            # 1. Check pip dependencies
            _check_and_install_deps(
                lambda msg: self.after(
                    0, self.download_screen._set_status, msg, theme.AMBER))

            # 2. Check FFmpeg
            from skipman.ffmpeg_setup import ensure_ffmpeg
            try:
                ensure_ffmpeg(
                    lambda msg: self.after(
                        0, self.download_screen._set_status, msg, theme.AMBER))
            except RuntimeError as e:
                self.after(
                    0, self.download_screen._set_status, str(e), theme.ERROR)
                return

            self.after(
                0, self.download_screen._set_status, "Ready.", theme.GREEN)

        threading.Thread(target=_check, daemon=True).start()

    # ── Screen Switching ────────────────────────────────────────────────────
    def show_download_screen(self):
        """Show the download/queue screen."""
        self.edit_screen.pack_forget()
        self.download_screen.pack(fill="both", expand=True)

    def show_edit_screen(self, song_info):
        """Show the edit screen with the given song metadata."""
        self.current_song = song_info
        self.download_screen.pack_forget()
        self.edit_screen.load_song(song_info)
        self.edit_screen.pack(fill="both", expand=True)

    def on_edit_done(self):
        """Called when the user finishes editing. Process next or go back."""
        if self.queue:
            self.show_download_screen()
            # Small delay so the screen renders before starting download
            self.after(300, self.download_screen.process_next)
        else:
            self.show_download_screen()
            self.download_screen._set_status(
                "All done! Add more URLs to continue.", theme.GREEN)
