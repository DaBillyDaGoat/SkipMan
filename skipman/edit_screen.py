# ── Edit Screen — Metadata, Artwork, iTunes Upload ──────────────────────────

import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import io

from skipman import theme


class EditScreen(tk.Frame):
    """Screen 2: edit song metadata, manage artwork, upload to Apple Music."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=theme.BG_DARK)
        self.app = app
        self.song_info = None
        self.artwork_path = None      # Path to artwork file (custom or downloaded thumb)
        self.has_artwork = False
        self.artwork_tk = None        # Keep reference to prevent GC
        self._thumb_temp = None       # Temp file for downloaded thumbnail
        self._build_ui()

    # ── Build UI ────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        tk.Label(
            self, text="// EDIT SONG", font=theme.FONT_HEADER,
            bg=theme.BG_DARK, fg=theme.GREEN,
        ).pack(padx=20, pady=(16, 0), anchor="w")

        tk.Frame(self, height=2, bg=theme.BORDER_MID).pack(
            fill="x", padx=20, pady=(8, 10))

        # ── Main Content — two columns ─────────────────────────────────────
        content = tk.Frame(self, bg=theme.BG_DARK)
        content.pack(fill="both", expand=True, padx=20)

        # LEFT: Artwork
        left = tk.Frame(content, bg=theme.BG_DARK, width=220)
        left.pack(side="left", fill="y", padx=(0, 16))
        left.pack_propagate(False)

        tk.Label(
            left, text="ARTWORK", **theme.label_style(muted=True),
        ).pack(anchor="w")

        self.art_canvas = tk.Canvas(
            left, width=200, height=200,
            bg=theme.BG_INPUT, relief="sunken", bd=2, highlightthickness=0,
        )
        self.art_canvas.pack(pady=(4, 8))
        self.art_placeholder = self.art_canvas.create_text(
            100, 100, text="NO ART", font=theme.FONT_MAIN, fill=theme.MUTED,
        )

        tk.Button(
            left, text="UPLOAD ART", padx=8, pady=3,
            **theme.button_style(), command=self._upload_artwork,
        ).pack(fill="x", pady=(0, 4))

        tk.Button(
            left, text="NO ARTWORK", padx=8, pady=3,
            **theme.button_style(), command=self._clear_artwork,
        ).pack(fill="x")

        # RIGHT: Metadata fields
        right = tk.Frame(content, bg=theme.BG_DARK)
        right.pack(side="left", fill="both", expand=True)

        # Title
        tk.Label(right, text="TITLE", **theme.label_style(muted=True)).pack(anchor="w")
        self.title_entry = tk.Entry(right, **theme.entry_style())
        self.title_entry.pack(fill="x", ipady=5, pady=(2, 10))

        # Artist
        tk.Label(right, text="ARTIST", **theme.label_style(muted=True)).pack(anchor="w")
        self.artist_entry = tk.Entry(right, **theme.entry_style())
        self.artist_entry.pack(fill="x", ipady=5, pady=(2, 10))

        # Album
        tk.Label(right, text="ALBUM", **theme.label_style(muted=True)).pack(anchor="w")
        self.album_entry = tk.Entry(right, **theme.entry_style())
        self.album_entry.pack(fill="x", ipady=5, pady=(2, 10))

        # File path display
        self.file_var = tk.StringVar(value="")
        tk.Label(
            right, textvariable=self.file_var,
            font=theme.FONT_STATUS, bg=theme.BG_DARK, fg=theme.MUTED,
            anchor="w", wraplength=350,
        ).pack(fill="x", pady=(8, 0), anchor="w")

        # ── Divider ────────────────────────────────────────────────────────
        tk.Frame(self, height=2, bg=theme.BORDER_MID).pack(
            fill="x", padx=20, pady=(8, 10))

        # ── Action Buttons ─────────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=theme.BG_DARK)
        btn_frame.pack(fill="x", padx=20, pady=(0, 6))

        self.save_btn = tk.Button(
            btn_frame, text="SAVE TAGS", padx=14, pady=5,
            **theme.button_style(), command=self._save,
        )
        self.save_btn.pack(side="left", padx=(0, 6))

        self.upload_btn = tk.Button(
            btn_frame, text="\u266b  UPLOAD TO APPLE MUSIC", padx=14, pady=5,
            **theme.button_style(accent=True), command=self._upload_to_itunes,
        )
        self.upload_btn.pack(side="left", padx=(0, 6))

        self.skip_btn = tk.Button(
            btn_frame, text="SKIP >>", padx=14, pady=5,
            **theme.button_style(), command=self._skip,
        )
        self.skip_btn.pack(side="right")

        self.back_btn = tk.Button(
            btn_frame, text="<< BACK", padx=14, pady=5,
            **theme.button_style(), command=self._back,
        )
        self.back_btn.pack(side="right", padx=(0, 6))

        # ── Status ─────────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            self, textvariable=self.status_var,
            font=theme.FONT_SMALL, bg=theme.BG_DARK, fg=theme.MUTED,
            anchor="w", wraplength=600,
        )
        self.status_label.pack(fill="x", padx=20, pady=(0, 6))

        # ── Bottom Status Bar ──────────────────────────────────────────────
        status_bar = tk.Frame(self, bg=theme.BG_PANEL, relief="sunken", bd=1)
        status_bar.pack(fill="x", side="bottom")
        self.bar_label = tk.Label(
            status_bar, text=" Edit Mode", font=theme.FONT_STATUS,
            bg=theme.BG_PANEL, fg=theme.MUTED, anchor="w",
        )
        self.bar_label.pack(side="left", padx=4, pady=2)

        self.queue_remaining = tk.Label(
            status_bar, text="", font=theme.FONT_STATUS,
            bg=theme.BG_PANEL, fg=theme.MUTED, anchor="e",
        )
        self.queue_remaining.pack(side="right", padx=4, pady=2)

    # ── Load Song Data ──────────────────────────────────────────────────────
    def load_song(self, song_info):
        """Populate the edit screen with downloaded song metadata."""
        self.song_info = song_info
        self.artwork_path = None
        self.has_artwork = False
        self._thumb_temp = None

        # Fill text fields
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, song_info.get("title", ""))

        self.artist_entry.delete(0, "end")
        self.artist_entry.insert(0, song_info.get("artist", ""))

        self.album_entry.delete(0, "end")
        self.album_entry.insert(0, song_info.get("album", ""))

        fp = song_info.get("file_path", "")
        self.file_var.set(f"File: {fp}")

        # Queue counter
        remaining = len(self.app.queue)
        self.queue_remaining.config(
            text=f"{remaining} more in queue" if remaining else "Last song",
        )

        # Load thumbnail
        thumb_url = song_info.get("thumbnail_url", "")
        if thumb_url:
            self._load_thumbnail(thumb_url)
        else:
            self._show_no_art()

        self._set_status(
            "Edit metadata, then SAVE or UPLOAD TO APPLE MUSIC.", theme.MUTED,
        )

    # ── Artwork ─────────────────────────────────────────────────────────────
    def _load_thumbnail(self, url):
        """Download thumbnail in background thread and display it."""
        self._show_loading_art()

        def _fetch():
            try:
                import requests
                from PIL import Image

                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                raw = resp.content

                # Save full-res thumbnail to temp file for ID3 embedding
                save_dir = os.path.dirname(
                    self.song_info.get("file_path", ""))
                if not save_dir or not os.path.isdir(save_dir):
                    save_dir = self.app.save_dir
                temp_path = os.path.join(save_dir, ".skipman_thumb.jpg")
                img_full = Image.open(io.BytesIO(raw))
                img_full.save(temp_path, "JPEG", quality=95)
                self._thumb_temp = temp_path

                # Resize for display
                display = img_full.resize((196, 196), Image.LANCZOS)
                self.after(0, self._display_artwork, display, temp_path)
            except Exception:
                self.after(0, self._show_no_art)

        threading.Thread(target=_fetch, daemon=True).start()

    def _display_artwork(self, pil_img, path=None):
        """Show a PIL image on the artwork canvas."""
        from PIL import ImageTk
        self.artwork_tk = ImageTk.PhotoImage(pil_img)
        self.art_canvas.delete("all")
        self.art_canvas.create_image(100, 100, image=self.artwork_tk)
        if path:
            self.artwork_path = path
        self.has_artwork = True

    def _show_no_art(self):
        self.art_canvas.delete("all")
        self.art_canvas.create_text(
            100, 100, text="NO ART",
            font=theme.FONT_MAIN, fill=theme.MUTED,
        )
        self.has_artwork = False
        self.artwork_path = None

    def _show_loading_art(self):
        self.art_canvas.delete("all")
        self.art_canvas.create_text(
            100, 100, text="Loading...",
            font=theme.FONT_SMALL, fill=theme.AMBER,
        )

    def _upload_artwork(self):
        """Open file dialog to select custom artwork."""
        path = filedialog.askopenfilename(
            title="Select Artwork",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        try:
            from PIL import Image
            img = Image.open(path)
            display = img.resize((196, 196), Image.LANCZOS)
            self._display_artwork(display, path)
            self._set_status("Artwork loaded.", theme.GREEN)
        except Exception as e:
            self._set_status(f"Failed to load image: {e}", theme.ERROR)

    def _clear_artwork(self):
        self._show_no_art()
        self._set_status("Artwork cleared.", theme.MUTED)

    # ── Actions ─────────────────────────────────────────────────────────────
    def _save(self):
        """Write ID3 tags (and artwork) to the MP3 file."""
        from skipman.metadata import write_tags

        fp = self.song_info.get("file_path", "")
        if not os.path.exists(fp):
            self._set_status("Error: MP3 file not found!", theme.ERROR)
            return

        try:
            write_tags(
                fp,
                title=self.title_entry.get(),
                artist=self.artist_entry.get(),
                album=self.album_entry.get(),
                artwork_path=self.artwork_path if self.has_artwork else None,
                clear_artwork=not self.has_artwork,
            )
            self._set_status("Tags saved!", theme.SUCCESS)
            return True
        except Exception as e:
            self._set_status(f"Error saving tags: {e}", theme.ERROR)
            return False

    def _upload_to_itunes(self):
        """Save tags then add to iTunes library."""
        # Save tags first
        saved = self._save()
        if saved is False:
            return

        fp = self.song_info.get("file_path", "")

        self.upload_btn.config(state="disabled", text="Uploading\u2026")
        self._set_status("Adding to iTunes library\u2026", theme.AMBER)

        def _do_upload():
            try:
                from skipman.itunes import add_to_itunes
                success, msg = add_to_itunes(fp)
                self.after(0, self._upload_done, msg, None)
            except Exception as e:
                self.after(0, self._upload_done, None, str(e))

        threading.Thread(target=_do_upload, daemon=True).start()

    def _upload_done(self, msg, error):
        self.upload_btn.config(
            state="normal", text="\u266b  UPLOAD TO APPLE MUSIC")
        if error:
            self._set_status(f"iTunes error: {error}", theme.ERROR)
        else:
            self._set_status(msg, theme.SUCCESS)
            # Auto-advance to next song after a brief pause
            if self.app.queue:
                self._set_status(
                    f"{msg}  \u2014  Next song in 2s...", theme.SUCCESS)
                self.after(2000, self._advance_queue)

    def _skip(self):
        """Skip this song without saving. Move to next in queue."""
        self._cleanup_temp()
        self.app.on_edit_done()

    def _back(self):
        """Return to download screen without processing next."""
        self._cleanup_temp()
        self.app.show_download_screen()

    def _advance_queue(self):
        """Move to the next song in queue."""
        self._cleanup_temp()
        self.app.on_edit_done()

    def _cleanup_temp(self):
        """Remove temporary thumbnail file."""
        if self._thumb_temp and os.path.exists(self._thumb_temp):
            try:
                os.remove(self._thumb_temp)
            except OSError:
                pass

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _set_status(self, msg, color=None):
        self.status_var.set(msg)
        if color:
            self.status_label.config(fg=color)
