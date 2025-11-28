import os
import re
import customtkinter as ctk
from tkinter import filedialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"}


def get_video_files(folder: str):
    """Return full paths of video files in folder."""
    files = []
    for name in os.listdir(folder):
        full = os.path.join(folder, name)
        if os.path.isfile(full):
            ext = os.path.splitext(name)[1].lower()
            if ext in VIDEO_EXTS:
                files.append(full)
    return files


def normalize_show_name(raw: str) -> str:
    """
    Normalize a show/movie name into OCD-friendly dotted form:

    'South Park' -> 'South.Park'
    'The_Walking-Dead' -> 'The.Walking.Dead'
    """
    raw = raw.strip()
    if not raw:
        return ""
    # Replace spaces/underscores with dots
    name = re.sub(r'[\s_]+', '.', raw)
    # Replace any other non-word (except .) with dots
    name = re.sub(r'[^\w.]+', '.', name)
    # Collapse repeated dots
    name = re.sub(r'\.+', '.', name)
    return name.strip('.')


def guess_show_name(folder_path: str) -> str:
    """
    Try to guess the show/movie name from the folder structure.

    Typical layout:
      .../South Park/Season 01/  -> 'South.Park'
      .../The Walking Dead/Season 2/ -> 'The.Walking.Dead'
      .../South Park The End Of Obesity 2024/ -> 'South.Park.The.End.Of.Obesity.2024'
    """
    folder_name = os.path.basename(folder_path)
    parent_name = os.path.basename(os.path.dirname(folder_path))

    # Strip trailing season markers from the folder name
    # e.g. "South Park Season 01" -> "South Park"
    tmp = re.sub(r'(?i)[.\s_-]*season[.\s_-]*\d+$', '', folder_name)
    tmp = re.sub(r'[.\s_-]*[sS]\d{1,2}$', '', tmp)
    candidate = tmp.strip(" .-_")

    # If candidate still looks like a proper name, use it.
    # If it's empty or just "Season", fall back to parent folder.
    if candidate and candidate.lower() != "season":
        base = candidate
    else:
        base = parent_name

    return normalize_show_name(base)


def extract_season_number_from_folder(folder_path: str) -> int:
    """
    Guess season from folder name:

      'Season 01', 'Season 1', 'S01', 's5', 'South Park Season 10'

    Fallback is 1.
    """
    name = os.path.basename(folder_path)

    # Season 01 / season 1
    m = re.search(r'[sS]eason[^\d]*(\d+)', name)
    if m:
        try:
            return max(1, int(m.group(1)))
        except ValueError:
            pass

    # S01 / s01 / S1
    m = re.search(r'[sS](\d{1,2})', name)
    if m:
        try:
            return max(1, int(m.group(1)))
        except ValueError:
            pass

    # Any numbers at all – take last group
    nums = re.findall(r'(\d+)', name)
    if nums:
        try:
            return max(1, int(nums[-1]))
        except ValueError:
            pass

    return 1


def extract_episode_number(filename: str):
    """
    Extract episode number from ANYWHERE in the filename.

    Supports:
      'The.Walking.Dead.S01E01.720p...' -> 1
      'Show.1x02.1080p...'             -> 2
      'Show - Ep 03 - title'           -> 3
      '01 Cartman Gets an Anal Probe'  -> 1
      'MyShow.720p.05.mkv'             -> 5 (last 1–2 digit group)
    """
    base = os.path.splitext(os.path.basename(filename))[0]

    # Pattern 1: SxxEyy or s1e2 anywhere
    m = re.search(r'[sS](\d{1,2})[ ._-]*[eE](\d{1,2})', base)
    if m:
        try:
            return int(m.group(2))
        except ValueError:
            pass

    # Pattern 2: 1x02 style
    m = re.search(r'\b(\d{1,2})[xX](\d{1,2})\b', base)
    if m:
        try:
            return int(m.group(2))
        except ValueError:
            pass

    # Pattern 3: Ep 03 / E03 / EP03
    m = re.search(r'[eE][pP]?[ ._-]?(\d{1,2})\b', base)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass

    # Pattern 4: leading digits at start
    m = re.match(r'\s*(\d+)', base)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass

    # Pattern 5: any 1–2 digit group, take the LAST one (ignores 1080/2160/etc)
    nums = re.findall(r'(\d{1,2})', base)
    if nums:
        try:
            return int(nums[-1])
        except ValueError:
            pass

    return None


def guess_season_from_files(video_paths):
    """
    If folder name doesn't give season, try reading SxxEyy from filenames.
    """
    for path in video_paths:
        base = os.path.splitext(os.path.basename(path))[0]
        m = re.search(r'[sS](\d{1,2})[ ._-]*[eE](\d{1,2})', base)
        if m:
            try:
                return max(1, int(m.group(1)))
            except ValueError:
                pass
    return None


def build_and_verify_episodes(video_paths):
    """
    Returns (sorted_items, error_message)

    sorted_items: list[(episode_number, path)]
    error_message: None if OK, otherwise string describing the problem.
    """
    items = []
    unparsed = []

    for path in video_paths:
        ep = extract_episode_number(path)
        if ep is None:
            unparsed.append(os.path.basename(path))
        else:
            items.append((ep, path))

    if unparsed:
        return None, (
            "These files could not be parsed for an episode number:\n"
            + "\n".join(unparsed)
        )

    nums = [ep for ep, _ in items]
    unique_nums = set(nums)

    # Duplicates
    duplicates = sorted({n for n in unique_nums if nums.count(n) > 1})
    if duplicates:
        return None, (
            "Duplicate episode numbers found (fix manually before renaming):\n"
            + ", ".join(f"{n:02d}" for n in duplicates)
        )

    # Gap-check
    sorted_nums = sorted(unique_nums)
    first = sorted_nums[0]
    last = sorted_nums[-1]

    expected = set(range(first, last + 1))
    missing = sorted(expected - unique_nums)
    if missing:
        return None, (
            "Missing episode numbers in sequence (fix manually before renaming):\n"
            + ", ".join(f"{n:02d}" for n in missing)
        )

    # All good, sort by episode number
    sorted_items = sorted(items, key=lambda t: t[0])
    return sorted_items, None


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.folder_path = None
        self.items = None       # (ep_num, path) for single TV season
        self.multi_items = None # (season, ep_num, path) for multi-season
        self.season = 1
        self.mode = "tv"        # "tv", "movie", or "multi"
        self.movie_path = None

        self.title("OCD MP4 Renamer (Show.sxx.exx / Movie)")
        self.geometry("800x520")

        # ---- TOP: HEADER ----
        header = ctk.CTkLabel(
            self,
            text="Folder → auto-detect TV season(s) or movie → OCD names",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        header.pack(padx=10, pady=(10, 5))

        # ---- CONTROLS FRAME ----
        controls = ctk.CTkFrame(self)
        controls.pack(padx=10, pady=5, fill="x")

        self.choose_btn = ctk.CTkButton(
            controls,
            text="Choose Folder",
            command=self.choose_folder
        )
        self.choose_btn.pack(side="left", padx=10, pady=10)

        self.folder_label = ctk.CTkLabel(
            controls,
            text="No folder selected",
            anchor="w"
        )
        self.folder_label.pack(side="left", padx=10, pady=10, fill="x", expand=True)

        # Right side: Mode / Title entry / Season
        self.mode_label = ctk.CTkLabel(
            controls,
            text="Mode: ?"
        )
        self.mode_label.pack(side="right", padx=10, pady=10)

        self.show_label = ctk.CTkLabel(
            controls,
            text="Title:"
        )
        self.show_label.pack(side="right", padx=10, pady=10)

        self.show_entry = ctk.CTkEntry(
            controls,
            width=220,
            placeholder_text="South.Park / The.Walking.Dead / Movie.Name"
        )
        self.show_entry.pack(side="right", padx=10, pady=10)

        self.season_label = ctk.CTkLabel(
            controls,
            text="Season: --"
        )
        self.season_label.pack(side="right", padx=10, pady=10)

        # ---- PREVIEW BOX ----
        preview_frame = ctk.CTkFrame(self)
        preview_frame.pack(padx=10, pady=5, fill="both", expand=True)

        preview_label = ctk.CTkLabel(
            preview_frame,
            text="Preview (old name → new name):",
            anchor="w"
        )
        preview_label.pack(padx=10, pady=(10, 5), fill="x")

        self.preview_box = ctk.CTkTextbox(
            preview_frame,
            wrap="none"
        )
        self.preview_box.pack(padx=10, pady=(0, 10), fill="both", expand=True)

        # ---- BOTTOM: STATUS + RENAME ----
        bottom = ctk.CTkFrame(self)
        bottom.pack(padx=10, pady=(0, 10), fill="x")

        self.status_label = ctk.CTkLabel(
            bottom,
            text="Select a folder to start.",
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10, pady=10, fill="x", expand=True)

        self.rename_btn = ctk.CTkButton(
            bottom,
            text="Rename",
            state="disabled",
            command=self.rename_files
        )
        self.rename_btn.pack(side="right", padx=10, pady=10)

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        self.folder_path = folder
        self.folder_label.configure(text=folder)

        # Base season guess from folder (used for single-season mode)
        self.season = extract_season_number_from_folder(folder)
        self.season_label.configure(text=f"Season: {self.season:02d}")

        # Auto-guess title (show or movie) and fill entry (can override)
        auto_title = guess_show_name(folder)
        self.show_entry.delete(0, "end")
        if auto_title:
            self.show_entry.insert(0, auto_title)

        # Build preview
        self.build_preview()

    def build_preview(self):
        self.preview_box.delete("1.0", "end")
        self.rename_btn.configure(state="disabled")
        self.items = None
        self.multi_items = None
        self.movie_path = None

        if not self.folder_path:
            self.status_label.configure(text="No folder selected.", text_color="red")
            self.mode_label.configure(text="Mode: ?")
            return

        videos = get_video_files(self.folder_path)

        # --- CASE 1: Folder itself holds videos (movie or single season) ---
        if videos:
            # If possible, override season from SxxEyy patterns in filenames
            season_from_files = guess_season_from_files(videos)
            if season_from_files is not None:
                self.season = season_from_files
                self.season_label.configure(text=f"Season: {self.season:02d}")

            # Decide mode: 1 video -> treat as movie, multiple -> TV season
            if len(videos) == 1:
                self.mode = "movie"
                self.mode_label.configure(text="Mode: MOVIE")
                self.build_movie_preview(videos[0])
            else:
                self.mode = "tv"
                self.mode_label.configure(text="Mode: TV SEASON")
                self.build_tv_preview(videos)
            return

        # --- CASE 2: No videos directly, try multi-season under subfolders ---
        subfolders = [
            os.path.join(self.folder_path, name)
            for name in os.listdir(self.folder_path)
            if os.path.isdir(os.path.join(self.folder_path, name))
        ]

        season_folders = []
        for sf in sorted(subfolders):
            vids = get_video_files(sf)
            if vids:
                season_folders.append((sf, vids))

        if not season_folders:
            self.status_label.configure(
                text="No video files found in this folder or its season subfolders.",
                text_color="red"
            )
            self.mode_label.configure(text="Mode: ?")
            self.season_label.configure(text="Season: --")
            return

        self.mode = "multi"
        self.mode_label.configure(text="Mode: TV MULTI-SEASON")
        self.season_label.configure(text="Season: multi")
        self.build_multi_tv_preview(season_folders)

    def build_movie_preview(self, video_path: str):
        """Preview renaming for a single movie file."""
        self.movie_path = video_path

        raw_title = self.show_entry.get().strip()
        title = normalize_show_name(raw_title) or guess_show_name(self.folder_path)
        title = normalize_show_name(title)

        # Push normalized value back into entry
        self.show_entry.delete(0, "end")
        if title:
            self.show_entry.insert(0, title)

        old_name = os.path.basename(video_path)
        ext = os.path.splitext(video_path)[1].lower() or ".mp4"

        if title:
            new_name = f"{title}{ext}"
        else:
            # If we somehow have no title, keep original name
            new_name = old_name

        self.preview_box.insert("end", f"Title (movie): {title or '(none – keeping base name)'}\n")
        self.preview_box.insert("end", f"Old file: {old_name}\n")
        self.preview_box.insert("end", f"New file: {new_name}\n")

        self.status_label.configure(
            text="Movie detected. Review then click Rename.",
            text_color="green"
        )
        self.rename_btn.configure(state="normal")

    def build_tv_preview(self, videos):
        """Preview renaming for a single TV season folder."""
        items, error = build_and_verify_episodes(videos)
        if error:
            # Show error in preview + status, don't allow rename
            self.preview_box.insert("end", error + "\n\nNo files were renamed.\n")
            self.status_label.configure(text="ERROR – see preview box.", text_color="red")
            self.items = None
            return

        self.items = items
        season_str = f"{self.season:02d}"

        # Normalize whatever is in the entry right now
        raw_show = self.show_entry.get().strip()
        show_name = normalize_show_name(raw_show)

        # Push normalized value back into the entry
        self.show_entry.delete(0, "end")
        if show_name:
            self.show_entry.insert(0, show_name)

        self.preview_box.insert("end", f"Show name: {show_name or '(none)'}\n")
        self.preview_box.insert("end", f"Season: {season_str}\n")
        self.preview_box.insert("end", f"Total episodes: {len(items)}\n\n")

        for ep_num, path in items:
            old_name = os.path.basename(path)
            ext = os.path.splitext(path)[1].lower() or ".mp4"
            if show_name:
                new_name = f"{show_name}.s{season_str}.e{ep_num:02d}{ext}"
            else:
                new_name = f"s{season_str}e{ep_num:02d}{ext}"
            self.preview_box.insert("end", f"{old_name}  →  {new_name}\n")

        self.status_label.configure(
            text="TV season detected. Review preview, then click Rename.",
            text_color="green"
        )
        self.rename_btn.configure(state="normal")

    def build_multi_tv_preview(self, season_folders):
        """Preview renaming for a multi-season show under one parent folder."""
        self.multi_items = []

        # Normalize / guess show name from entry or parent folder
        raw_show = self.show_entry.get().strip()
        if not raw_show:
            raw_show = guess_show_name(self.folder_path)
        show_name = normalize_show_name(raw_show)

        self.show_entry.delete(0, "end")
        if show_name:
            self.show_entry.insert(0, show_name)

        self.preview_box.insert("end", f"Show name: {show_name or '(none)'}\n")

        total_eps = 0
        errors = []

        for season_folder, videos in season_folders:
            # Determine season number from folder name or filenames
            season = extract_season_number_from_folder(season_folder)
            season_from_files = guess_season_from_files(videos)
            if season_from_files is not None:
                season = season_from_files

            season_str = f"{season:02d}"
            base_name = os.path.basename(season_folder)

            items, error = build_and_verify_episodes(videos)
            if error:
                errors.append(f"[{base_name} (Season {season_str})]\n{error}")
                continue

            self.preview_box.insert("end", f"\n=== Season {season_str} ({base_name}) ===\n")
            self.preview_box.insert("end", f"Total episodes: {len(items)}\n")

            for ep_num, path in items:
                ext = os.path.splitext(path)[1].lower() or ".mp4"
                if show_name:
                    new_name = f"{show_name}.s{season_str}.e{ep_num:02d}{ext}"
                else:
                    new_name = f"s{season_str}e{ep_num:02d}{ext}"
                old_name = os.path.basename(path)
                self.preview_box.insert("end", f"{old_name}  →  {new_name}\n")

                self.multi_items.append((season, ep_num, path))
                total_eps += 1

        if errors:
            self.preview_box.insert("end", "\nERRORS:\n------\n")
            for e in errors:
                self.preview_box.insert("end", e + "\n\n")
            self.status_label.configure(
                text="ERROR – some season folders had problems. Fix them and try again.",
                text_color="red"
            )
            self.multi_items = None
            self.rename_btn.configure(state="disabled")
            return

        if not self.multi_items:
            self.status_label.configure(
                text="No valid episodes found in season subfolders.",
                text_color="red"
            )
            self.rename_btn.configure(state="disabled")
            return

        self.preview_box.insert("end", f"\nTOTAL episodes across all seasons: {total_eps}\n")
        self.status_label.configure(
            text="Multi-season TV detected. Review preview, then click Rename.",
            text_color="green"
        )
        self.rename_btn.configure(state="normal")

    def rename_files(self):
        if not self.folder_path:
            self.status_label.configure(text="No folder selected.", text_color="red")
            return

        # MOVIE MODE
        if self.mode == "movie":
            if not self.movie_path:
                self.status_label.configure(text="No movie file to rename.", text_color="red")
                return

            raw_title = self.show_entry.get().strip()
            title = normalize_show_name(raw_title) or guess_show_name(self.folder_path)
            title = normalize_show_name(title)

            old_path = self.movie_path
            folder = os.path.dirname(old_path)
            old_name = os.path.basename(old_path)
            ext = os.path.splitext(old_path)[1].lower() or ".mp4"

            if title:
                base_new = f"{title}{ext}"
            else:
                self.status_label.configure(
                    text="No title set – leaving movie name as-is.",
                    text_color="orange"
                )
                return

            new_path = os.path.join(folder, base_new)

            if os.path.abspath(old_path) == os.path.abspath(new_path):
                self.status_label.configure(
                    text=f"Movie already named '{base_new}'. Nothing to do.",
                    text_color="green"
                )
                return

            candidate = new_path
            suffix = 1
            while os.path.exists(candidate):
                candidate_name = f"{title}_{suffix}{ext}"
                candidate = os.path.join(folder, candidate_name)
                suffix += 1

            os.rename(old_path, candidate)

            self.build_preview()  # refresh
            self.rename_btn.configure(state="disabled")
            self.status_label.configure(
                text=f"Movie renamed:\n{old_name} → {os.path.basename(candidate)}",
                text_color="green"
            )
            return

        # MULTI-SEASON TV MODE
        if self.mode == "multi":
            if not self.multi_items:
                self.status_label.configure(text="Nothing to rename.", text_color="red")
                return

            raw_show = self.show_entry.get().strip()
            if not raw_show:
                raw_show = guess_show_name(self.folder_path)
            show_name = normalize_show_name(raw_show)

            # Push normalized value back into the entry
            self.show_entry.delete(0, "end")
            if show_name:
                self.show_entry.insert(0, show_name)

            # For status example
            first_season = min(season for season, _, _ in self.multi_items)
            first_ext = os.path.splitext(self.multi_items[0][2])[1].lower() or ".mp4"

            renamed_count = 0

            for season, ep_num, old_path in self.multi_items:
                folder = os.path.dirname(old_path)
                ext = os.path.splitext(old_path)[1].lower() or ".mp4"
                season_str = f"{season:02d}"

                if show_name:
                    base_new = f"{show_name}.s{season_str}.e{ep_num:02d}{ext}"
                else:
                    base_new = f"s{season_str}e{ep_num:02d}{ext}"

                new_path = os.path.join(folder, base_new)

                if os.path.abspath(old_path) == os.path.abspath(new_path):
                    continue

                candidate = new_path
                suffix = 1
                # Avoid overwwriting anything that already exists.
                while os.path.exists(candidate):
                    if show_name:
                        candidate_name = f"{show_name}.s{season_str}.e{ep_num:02d}_{suffix}{ext}"
                    else:
                        candidate_name = f"s{season_str}e{ep_num:02d}_{suffix}{ext}"
                    candidate = os.path.join(folder, candidate_name)
                    suffix += 1

                os.rename(old_path, candidate)
                renamed_count += 1

            # Rebuild preview with new names
            self.build_preview()
            self.rename_btn.configure(state="disabled")

            example = (
                f"{show_name}.s{first_season:02d}.e01{first_ext}"
                if show_name
                else f"s{first_season:02d}e01{first_ext}"
            )
            self.status_label.configure(
                text=f"Renamed {renamed_count} file(s) across all seasons to '{example}' style.",
                text_color="green"
            )
            return

        # SINGLE-SEASON TV MODE
        if not self.items:
            self.status_label.configure(text="Nothing to rename.", text_color="red")
            return

        season_str = f"{self.season:02d}"
        renamed_count = 0

        # Normalize show name again at rename time
        raw_show = self.show_entry.get().strip()
        show_name = normalize_show_name(raw_show)

        # Push normalized value back into the entry (so UI matches)
        self.show_entry.delete(0, "end")
        if show_name:
            self.show_entry.insert(0, show_name)

        # Example extension based on first item
        first_ext = os.path.splitext(self.items[0][1])[1].lower() or ".mp4"

        for ep_num, old_path in self.items:
            folder = os.path.dirname(old_path)
            ext = os.path.splitext(old_path)[1].lower() or ".mp4"

            if show_name:
                base_new = f"{show_name}.s{season_str}.e{ep_num:02d}{ext}"
            else:
                base_new = f"s{season_str}e{ep_num:02d}{ext}"

            new_path = os.path.join(folder, base_new)

            if os.path.abspath(old_path) == os.path.abspath(new_path):
                continue

            candidate = new_path
            suffix = 1
            # Avoid overwriting anything that already exists.
            while os.path.exists(candidate):
                if show_name:
                    candidate_name = f"{show_name}.s{season_str}.e{ep_num:02d}_{suffix}{ext}"
                else:
                    candidate_name = f"s{season_str}e{ep_num:02d}_{suffix}{ext}"
                candidate = os.path.join(folder, candidate_name)
                suffix += 1

            os.rename(old_path, candidate)
            renamed_count += 1

        # Rebuild preview with new names
        self.build_preview()
        self.rename_btn.configure(state="disabled")

        example = (
            f"{show_name}.s{season_str}.e01{first_ext}" if show_name else f"s{season_str}e01{first_ext}"
        )
        self.status_label.configure(
            text=f"Renamed {renamed_count} file(s) to '{example}' style.",
            text_color="green"
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()
