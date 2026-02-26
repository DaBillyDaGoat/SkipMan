# ── Download Screen — Queue + Download UI ───────────────────────────────────

import tkinter as tk
from tkinter import filedialog
import threading

from skipman import theme


class DownloadScreen(tk.Frame):
    """Screen 1: paste URLs, manage queue, download MP3s."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=theme.BG_DARK)
        self.app = app
        self._build_ui()

    # ── Build UI ────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=theme.BG_DARK)
        hdr.pack(fill="x", padx=20, pady=(16, 0))

        tk.Label(
            hdr, text="// SKIPMAN v1.0", font=theme.FONT_HEADER,
            bg=theme.BG_DARK, fg=theme.GREEN,
        ).pack(anchor="w")

        tk.Label(
            hdr, text="YouTube  \u00b7  SoundCloud  \u00b7  and more",
            font=theme.FONT_SMALL, bg=theme.BG_DARK, fg=theme.MUTED,
        ).pack(anchor="w")

        tk.Frame(self, height=2, bg=theme.BORDER_MID).pack(
            fill="x", padx=20, pady=(10, 10))

        # ── URL Input Row ───────────────────────────────────────────────────
        tk.Label(
            self, text="PASTE URL", **theme.label_style(muted=True),
        ).pack(padx=20, anchor="w")

        url_row = tk.Frame(self, bg=theme.BG_DARK)
        url_row.pack(fill="x", padx=20, pady=(2, 8))

        self.url_entry = tk.Entry(url_row, **theme.entry_style())
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=5)
        self.url_entry.bind("<Return>", lambda e: self._add_to_queue())

        self.add_btn = tk.Button(
            url_row, text="ADD", padx=14, pady=3,
            **theme.button_style(), command=self._add_to_queue,
        )
        self.add_btn.pack(side="right", padx=(8, 0))

        # ── Save Folder ────────────────────────────────────────────────────
        tk.Label(
            self, text="SAVE TO", **theme.label_style(muted=True),
        ).pack(padx=20, anchor="w")

        folder_row = tk.Frame(self, bg=theme.BG_DARK)
        folder_row.pack(fill="x", padx=20, pady=(2, 8))

        self.folder_var = tk.StringVar(value=self.app.save_dir)
        tk.Label(
            folder_row, textvariable=self.folder_var,
            font=theme.FONT_SMALL, bg=theme.BG_INPUT, fg=theme.TEXT_LIGHT,
            anchor="w", relief="sunken", bd=2,
        ).pack(side="left", fill="x", expand=True, ipady=3)

        tk.Button(
            folder_row, text="...", padx=10, pady=1,
            **theme.button_style(), command=self._browse,
        ).pack(side="right", padx=(8, 0))

        # ── Queue ───────────────────────────────────────────────────────────
        self.queue_label = tk.Label(
            self, text="QUEUE (0)", **theme.label_style(muted=True),
        )
        self.queue_label.pack(padx=20, anchor="w", pady=(4, 0))

        queue_frame = tk.Frame(self, bg=theme.BG_DARK)
        queue_frame.pack(fill="x", padx=20, pady=(2, 4))

        self.queue_listbox = tk.Listbox(
            queue_frame, font=theme.FONT_SMALL,
            bg=theme.BG_INPUT, fg=theme.TEXT_LIGHT,
            selectbackground=theme.GREEN, selectforeground=theme.TEXT_DARK,
            relief="sunken", bd=2, height=5, activestyle="none",
        )
        self.queue_listbox.pack(fill="x")

        # Queue buttons
        qbtn_row = tk.Frame(self, bg=theme.BG_DARK)
        qbtn_row.pack(fill="x", padx=20, pady=(0, 10))

        tk.Button(
            qbtn_row, text="REMOVE", padx=10, pady=2,
            **theme.button_style(), command=self._remove_selected,
        ).pack(side="left")

        tk.Button(
            qbtn_row, text="CLEAR ALL", padx=10, pady=2,
            **theme.button_style(), command=self._clear_queue,
        ).pack(side="left", padx=(8, 0))

        self.dl_btn = tk.Button(
            qbtn_row, text="\u25b6  DOWNLOAD", padx=16, pady=4,
            **theme.button_style(accent=True), command=self._start_download,
        )
        self.dl_btn.pack(side="right")

        # ── Progress Bar (segmented, chunky 90s style) ─────────────────────
        self.progress_canvas = tk.Canvas(
            self, height=18, bg=theme.BG_PANEL,
            relief="sunken", bd=2, highlightthickness=0,
        )
        self.progress_canvas.pack(fill="x", padx=20, pady=(0, 4))

        # ── Status ─────────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready.")
        self.status_label = tk.Label(
            self, textvariable=self.status_var,
            font=theme.FONT_SMALL, bg=theme.BG_DARK, fg=theme.MUTED,
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=20, pady=(0, 6))

        # ── Log ────────────────────────────────────────────────────────────
        tk.Frame(self, height=2, bg=theme.BORDER_MID).pack(
            fill="x", padx=20, pady=(0, 6))

        self.log = tk.Text(
            self, font=theme.FONT_SMALL, bg=theme.BG_INPUT, fg=theme.MUTED,
            relief="sunken", bd=2, height=4, state="disabled", wrap="word",
        )
        self.log.pack(fill="both", padx=20, pady=(0, 10), expand=True)

        # ── Bottom Status Bar (classic Windows) ────────────────────────────
        status_bar = tk.Frame(self, bg=theme.BG_PANEL, relief="sunken", bd=1)
        status_bar.pack(fill="x", side="bottom")
        tk.Label(
            status_bar, text=" SkipMan v1.0", font=theme.FONT_STATUS,
            bg=theme.BG_PANEL, fg=theme.MUTED, anchor="w",
        ).pack(side="left", padx=4, pady=2)

    # ── Queue Actions ───────────────────────────────────────────────────────
    def _add_to_queue(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        self.app.queue.append(url)
        self._refresh_queue_display()
        self.url_entry.delete(0, "end")
        self._set_status(f"Added to queue. ({len(self.app.queue)} total)", theme.GREEN)

    def _remove_selected(self):
        sel = self.queue_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.app.queue.pop(idx)
        self._refresh_queue_display()

    def _clear_queue(self):
        self.app.queue.clear()
        self._refresh_queue_display()
        self._set_status("Queue cleared.", theme.MUTED)

    def _refresh_queue_display(self):
        self.queue_listbox.delete(0, "end")
        for i, url in enumerate(self.app.queue):
            # Truncate long URLs for display
            display = url if len(url) < 65 else url[:62] + "..."
            self.queue_listbox.insert("end", f"  {i + 1}. {display}")
        self.queue_label.config(text=f"QUEUE ({len(self.app.queue)})")

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.app.save_dir)
        if d:
            self.app.save_dir = d
            self.folder_var.set(d)

    # ── Download ────────────────────────────────────────────────────────────
    def _start_download(self):
        if not self.app.queue:
            self._set_status("Add URLs to the queue first.", theme.ERROR)
            return
        self.process_next()

    def process_next(self):
        """Pop the first URL from the queue and download it."""
        if not self.app.queue:
            self._set_status("Queue empty. All done!", theme.GREEN)
            self.dl_btn.config(state="normal", text="\u25b6  DOWNLOAD")
            return

        url = self.app.queue.pop(0)
        self._refresh_queue_display()
        self.dl_btn.config(state="disabled", text="Downloading\u2026")
        self._set_status("Starting download\u2026", theme.MUTED)
        self._set_progress(0)

        threading.Thread(target=self._download, args=(url,), daemon=True).start()

    def _download(self, url):
        from skipman.downloader import download_song
        from skipman.ffmpeg_setup import get_ffmpeg_location

        ffmpeg_loc = get_ffmpeg_location()

        def progress_hook(d):
            if d["status"] == "downloading":
                pct_str = d.get("_percent_str", "0%").strip().replace("%", "")
                try:
                    pct = float(pct_str)
                    speed = d.get("_speed_str", "")
                    self.after(0, self._set_progress, pct)
                    self.after(0, self._set_status,
                               f"Downloading\u2026 {pct_str}%  {speed}", theme.MUTED)
                except ValueError:
                    pass
            elif d["status"] == "finished":
                self.after(0, self._set_progress, 100)
                self.after(0, self._set_status,
                           "Converting to MP3\u2026", theme.AMBER)

        try:
            result = download_song(
                url, self.app.save_dir,
                progress_callback=progress_hook,
                ffmpeg_location=ffmpeg_loc,
            )
            self.after(0, self._download_done, result, None)
        except Exception as e:
            self.after(0, self._download_done, None, str(e))

    def _download_done(self, result, error):
        self.dl_btn.config(state="normal", text="\u25b6  DOWNLOAD")
        if error:
            self._set_status(f"Error: {error}", theme.ERROR)
            self._log(f"[ERROR] {error}")
            self._set_progress(0)
            # If there are more items in queue, don't stop
            if self.app.queue:
                self._set_status(
                    f"Error: {error}  \u2014  Skipping to next in queue...",
                    theme.ERROR,
                )
                self.after(1500, self.process_next)
        else:
            title = result.get("title", "Unknown")
            self._set_status(f'Downloaded: "{title}"', theme.SUCCESS)
            self._log(f'[OK] "{title}.mp3"')
            self._set_progress(100)
            # Transition to edit screen
            self.after(500, self.app.show_edit_screen, result)

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _set_status(self, msg, color=None):
        self.status_var.set(msg)
        if color:
            self.status_label.config(fg=color)

    def _set_progress(self, pct):
        """Draw segmented progress bar (chunky 90s style)."""
        self.update_idletasks()
        w = self.progress_canvas.winfo_width()
        h = self.progress_canvas.winfo_height()
        self.progress_canvas.delete("seg")

        total_segs = 30
        gap = 2
        seg_w = max(1, (w - 6) / total_segs)
        filled = int(total_segs * pct / 100)

        for i in range(total_segs):
            x0 = 3 + i * seg_w + gap / 2
            x1 = x0 + seg_w - gap
            color = theme.GREEN if i < filled else theme.BG_DARK
            self.progress_canvas.create_rectangle(
                x0, 3, x1, h - 3, fill=color, outline="", tags="seg",
            )

    def _log(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.config(state="disabled")
