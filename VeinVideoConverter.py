# ------------------------------------------------------------------------
# VeinVideoConverter.py
# Created by Astroolean with love and appreciation for the game Vein...
# Converts any common video format to Vein-safe MP4 (H.264/AAC).
# ------------------------------------------------------------------------

import os
import json
import subprocess
import threading
import time
import customtkinter as ctk
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"}


# --------------------------------------------------------
# ffprobe helper
# --------------------------------------------------------
def ffprobe_info(path: str):
    """Run ffprobe and return parsed JSON, or None on failure."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        # ffprobe not installed / not in PATH
        return None

    if not result.stdout.strip():
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


# --------------------------------------------------------
# classification: SAFE_MP4 / NEED_CONVERT / ERROR
# --------------------------------------------------------
def classify_video(path: str):
    """
    Classify a video file:
      SAFE_MP4     = .mp4 container with h264 video + aac audio
      NEED_CONVERT = anything else that has valid streams
      ERROR        = ffprobe can't read valid streams
    """
    info = ffprobe_info(path)
    if not info:
        return ("ERROR", None, None)

    video = None
    audio = None

    for s in info.get("streams", []):
        stype = s.get("codec_type")
        if stype == "video" and video is None:
            video = s.get("codec_name")
        elif stype == "audio" and audio is None:
            audio = s.get("codec_name")

    # ffprobe saw no codecs at all
    if video is None and audio is None:
        return ("ERROR", video, audio)

    ext = os.path.splitext(path)[1].lower()

    if ext == ".mp4" and (video or "").lower() == "h264" and (audio or "").lower() == "aac":
        return ("SAFE_MP4", video, audio)

    return ("NEED_CONVERT", video, audio)


# --------------------------------------------------------
# convert one file → Vein-safe MP4
# --------------------------------------------------------
def convert_to_vein_mp4(src: str, dst: str, progress_callback):
    """
    Convert one file to Vein-friendly MP4 with progress updates + ETA.
    Uses libx264 only (no NVENC), in a very compatible H.264/AAC format:
      - H.264, yuv420p
      - CRF 20, preset medium (change to veryfast if you want more speed)
      - AAC 192k, stereo, 44.1kHz
      - +faststart for streaming
    progress_callback(pct, eta_seconds)
    Returns True on success, False on failure.
    """
    info = ffprobe_info(src)

    total_duration = 1.0
    if info and "format" in info and "duration" in info["format"]:
        try:
            d = float(info["format"]["duration"])
            if d > 0:
                total_duration = d
        except (ValueError, TypeError):
            pass

    cmd = [
        "ffmpeg", "-y", "-i", src,
        # VIDEO: super compatible H.264
        "-c:v", "libx264",
        "-preset", "veryfast",      # faster encodes
        "-crf", "20",
        "-pix_fmt", "yuv420p",    # critical for compatibility
        # AUDIO: plain AAC stereo 44.1kHz
        "-c:a", "aac",
        "-b:a", "192k",
        "-ac", "2",
        "-ar", "44100",
        # MP4 streaming friendly
        "-movflags", "+faststart",
        dst,
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        progress_callback(0.0, None)
        return False

    start_wall = time.time()

    # read progress from ffmpeg's stderr
    for line in proc.stderr:
        if "time=" in line:
            try:
                time_part = line.split("time=")[1].split()[0]
                h, m, s = time_part.split(":")
                current = float(h) * 3600 + float(m) * 60 + float(s)
                pct = max(0.0, min(100.0, (current / total_duration) * 100.0))

                now = time.time()
                elapsed_wall = now - start_wall
                eta_seconds = None
                if elapsed_wall > 0 and current > 0:
                    speed = current / elapsed_wall
                    if speed > 0:
                        remaining = max(0.0, total_duration - current)
                        eta_seconds = remaining / speed

                progress_callback(pct, eta_seconds)
            except Exception:
                continue

    proc.wait()

    success = proc.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 0
    if success:
        progress_callback(100.0, 0.0)
    else:
        progress_callback(0.0, None)

    return success


# --------------------------------------------------------
# GUI app
# --------------------------------------------------------
class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Vein Video Converter (→ Vein-safe MP4)")
        self.geometry("900x820")
        self.configure(bg="#111111")

        self.folder = None
        self.jobs = []  # list of dicts: {src, dst, status}

        # ---------- top bar ----------
        top = ctk.CTkFrame(self, fg_color="#181818")
        top.pack(fill="x", pady=(10, 5), padx=10)

        self.folder_label = ctk.CTkLabel(
            top,
            text="Drop folder here or click Browse",
            font=("Segoe UI", 18),
        )
        self.folder_label.pack(side="left", padx=20, pady=10)

        browse_btn = ctk.CTkButton(
            top,
            text="Browse",
            command=self.browse_folder,
            width=120,
        )
        browse_btn.pack(side="right", padx=20, pady=10)

        self.encoder_label = ctk.CTkLabel(
            self,
            text="Output: MP4 / H.264 (libx264) + AAC 192k, 44.1kHz stereo",
            font=("Segoe UI", 13),
        )
        self.encoder_label.pack(anchor="w", padx=20)

        # ---------- textbox ----------
        self.textbox = ctk.CTkTextbox(
            self,
            width=860,
            height=520,
            font=("Consolas", 14),
        )
        self.textbox.pack(padx=10, pady=10)

        self.textbox.tag_config("convert", foreground="#ffcc00")
        self.textbox.tag_config("skip", foreground="#00ff88")
        self.textbox.tag_config("error", foreground="#ff4444")
        self.textbox.tag_config("header", foreground="#66aaff")

        # ---------- progress ----------
        self.progress_label = ctk.CTkLabel(
            self,
            text="Progress: 0%",
            font=("Segoe UI", 16),
        )
        self.progress_label.pack(pady=(0, 5))

        self.progress_bar = ctk.CTkProgressBar(self, width=860)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(0, 15))

        # ---------- bottom buttons ----------
        bottom = ctk.CTkFrame(self, fg_color="#181818")
        bottom.pack(fill="x", padx=10, pady=(0, 10))

        self.rescan_button = ctk.CTkButton(
            bottom,
            text="Rescan Folder",
            command=self.scan_folder,
            width=160,
        )
        self.rescan_button.pack(side="left", padx=20, pady=10)

        self.convert_button = ctk.CTkButton(
            bottom,
            text="CONVERT ALL",
            command=self.start_convert_thread,
            fg_color="#cc3333",
            hover_color="#aa2222",
            width=220,
            height=40,
            font=("Segoe UI", 16, "bold"),
        )
        self.convert_button.pack(side="right", padx=20, pady=10)

    # ---------- thread-safe UI helpers ----------
    def append_text(self, text: str, tag: str | None = None):
        def _do():
            if tag:
                self.textbox.insert("end", text, tag)
            else:
                self.textbox.insert("end", text)
            self.textbox.see("end")
        self.after(0, _do)

    def update_progress(self, pct: float, eta_seconds):
        def _do():
            self.progress_bar.set(pct / 100.0)
            if eta_seconds is not None and eta_seconds > 0:
                total_seconds = int(eta_seconds + 0.5)
                mins, secs = divmod(total_seconds, 60)
                if mins >= 60:
                    hours, mins = divmod(mins, 60)
                    eta_str = f"{hours}h {mins}m"
                elif mins > 0:
                    eta_str = f"{mins}m {secs:02d}s"
                else:
                    eta_str = f"{secs}s"
                text = f"Progress: {pct:.1f}%  |  ETA: {eta_str}"
            else:
                text = f"Progress: {pct:.1f}%"
            self.progress_label.configure(text=text)
        self.after(0, _do)

    # ---------- folder selection ----------
    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder = path
            self.folder_label.configure(text=path)
            self.scan_folder()

    # ---------- scanning ----------
    def scan_folder(self):
        if not self.folder:
            messagebox.showinfo("Info", "Pick a folder first.")
            return

        self.jobs = []
        self.textbox.delete("1.0", "end")

        self.textbox.insert("end", f"Scanning: {self.folder}\n\n", "header")
        self.textbox.insert(
            "end",
            f"{'ACTION':<12} | {'FILE':<45} | {'VIDEO':<10} | {'AUDIO'}\n",
            "header",
        )
        self.textbox.insert("end", "-" * 90 + "\n")

        for name in sorted(os.listdir(self.folder)):
            full_path = os.path.join(self.folder, name)
            if not os.path.isfile(full_path):
                continue

            ext = os.path.splitext(name)[1].lower()
            if ext not in VIDEO_EXTS:
                continue

            status, vcodec, acodec = classify_video(full_path)

            if status == "SAFE_MP4":
                action = "SKIP"
                tag = "skip"
                dst = None
            elif status == "NEED_CONVERT":
                action = "CONVERT"
                tag = "convert"
                base = os.path.splitext(name)[0]      # <-- keeps your base name
                dst_name = base + ".mp4"              # <-- always .mp4
                dst = os.path.join(self.folder, "converted", dst_name)
                self.jobs.append({"src": full_path, "dst": dst, "name": dst_name})
            else:
                action = "ERROR"
                tag = "error"
                dst = None

            line = f"{action:<12} | {name:<45} | {str(vcodec):<10} | {str(acodec)}\n"
            self.textbox.insert("end", line, tag)

        self.textbox.insert(
            "end",
            f"\nFiles needing convert: {len(self.jobs)}\n",
            "header",
        )
        self.textbox.see("end")

    # ---------- converting ----------
    def start_convert_thread(self):
        t = threading.Thread(target=self.convert_all_worker, daemon=True)
        t.start()

    def convert_all_worker(self):
        if not self.folder:
            self.after(0, lambda: messagebox.showinfo("Info", "Pick a folder first."))
            return

        if not self.jobs:
            self.after(0, lambda: messagebox.showinfo("Info", "No files need converting. Scan first."))
            return

        out_dir = os.path.join(self.folder, "converted")
        os.makedirs(out_dir, exist_ok=True)

        self.append_text("\nStarting conversion...\n", "header")
        self.update_progress(0.0, None)

        total = len(self.jobs)

        for idx, job in enumerate(self.jobs, start=1):
            src = job["src"]
            dst = job["dst"]
            name = os.path.basename(dst)

            self.append_text(f"Converting {name} ({idx}/{total})...\n", "convert")

            ok = convert_to_vein_mp4(src, dst, self.update_progress)

            if ok:
                self.append_text(f"✔ Finished {name}\n", "skip")
            else:
                self.append_text(f"✖ FAILED {name}\n", "error")

        def _done():
            messagebox.showinfo("Done", "Finished converting videos.\nCheck the 'converted' folder.")
            self.update_progress(0.0, None)

        self.after(0, _done)


# --------------------------------------------------------
# MAIN
# --------------------------------------------------------
if __name__ == "__main__":
    app = App()
    app.mainloop()
