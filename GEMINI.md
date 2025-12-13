# Gemini Context & Instructions

## Project Preferences
- **Backups:** Always create a backup of a file before modifying it.
  - **Naming Convention:** `filename.ext.backup.YYYY-MM-DD-HH:MM:SS`

## Project Structure & Status
- **Bash Script (`quicktube.v1.sh`):** Functional, with support for YouTube and SVT Play (including series via `yt-dlp` fallback).
- **Python Port (`quicktube-py-dist/quicktube.py`):** The new main version for distribution.
  - **Features:** Same as Bash version but more robust (JSON handling, CSV parsing).
  - **Distribution:** Can be built into a standalone binary using PyInstaller.
  - **Bundled Tools:** Includes `gum`, `yt-dlp`, `svtplay-dl`.
  - **Auto-Update:** Can update binaries to user's local path (`~/.local/bin/quicktube_tools` on Linux, `%APPDATA%` on Windows).
  - **Cookie Support:** Allows using browser cookies (Chrome, Firefox, etc.) to bypass YouTube "Sign in" requirements.
  - **Main Menu:** Press Enter at startup to access tools and settings directly.

## Python Build Instructions
Located in `quicktube-py-dist/`:
- **Linux:** `./build_linux.sh` -> Output: `dist/quicktube`
- **macOS:** `./build_mac.sh` -> Output: `dist/quicktube-mac`
- **PyInstaller:** Bundles binaries from `bin/` and sets up `PATH` at runtime via `sys._MEIPASS`.

## Tool Cheat Sheet & Quirks

### svtplay-dl
**Usage:** `svtplay-dl [options] <URL>`
- **Quirk:** Modern versions may fail to scrape "series pages" (e.g., `/program-name`) with "No videos found".
- **Solution:** Use `yt-dlp` for parsing/downloading full series from series pages, or specific episodes. `svtplay-dl` works best for individual episode URLs or `--all-last`.

**Common Flags:**
- `-S`, `--subtitle`: Download subtitles.
- `-M`, `--merge-subtitle`: Merge subtitles into the video file (requires ffmpeg).
- `-A`, `--all-episodes`: Download all episodes (use with caution on series pages).
- `--all-last <N>`: Download the last N episodes (counts from end).

### yt-dlp
**Usage:** `yt-dlp [options] <URL>`
- **SVT Support:** Excellent for parsing series pages as playlists.
- **Downloading specific episodes:** `yt-dlp --playlist-items 1,2,5-10 <URL>`
- **Cookies:** `--cookies-from-browser chrome` (or firefox/safari/etc) is essential for bypassing login checks.

**Common Flags:**
- `-f <format>`: Format selection.
- `--embed-subs --write-subs --sub-langs all`: Best combo for subtitles.
- `-o <template>`: Output template.

## Dependencies
- `gum`: TUI utility.
- `yt-dlp`: Main downloader.
- `svtplay-dl`: Specialized downloader (bundled).
- `ffmpeg`: Required for merging (External dependency, NOT bundled).
- `mpv`: Media player (External dependency, NOT bundled).
