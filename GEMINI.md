# Gemini Context & Instructions

## Project Preferences
- **Backups:** Always create a backup of a file before modifying it.
  - **Naming Convention:** `filename.ext.backup.YYYY-MM-DD-HH:MM:SS`

## Tool Cheat Sheet

### svtplay-dl
**Usage:** `svtplay-dl [options] <URL>`

**Common Flags:**
- `-S`, `--subtitle`: Download subtitles.
- `-M`, `--merge-subtitle`: Merge subtitles into the video file (requires ffmpeg).
- `--force-subtitle`: Download *only* subtitles.
- `-A`, `--all-episodes`: Download all episodes of a program.
- `--all-last <N>`: Download the last N episodes.
- `--list-quality`: List available qualities and streams (DASH, HLS, etc.).
- `-q <bitrate>`, `--quality <bitrate>`: Select quality by bitrate.
- `-P <protocol>`, `--preferred <protocol>`: Prefer specific protocol (dash, hls, http, hds).
- `--only-audio`: Download audio only.
- `--output <filename>`: Specify output filename.

### yt-dlp
**Usage:** `yt-dlp [options] <URL>`

**Common Flags:**
- `-F`, `--list-formats`: List available formats.
- `-f <format>`, `--format <format>`: Select specific format code (e.g., `bestvideo+bestaudio` or `137+140`).
- `--merge-output-format <container>`: Merge video+audio into specific container (e.g., `mp4`, `mkv`).
- `-x`, `--extract-audio`: Convert video to audio.
- `--audio-format <format>`: Specify audio format (mp3, opus, m4a, etc.).
- `--embed-metadata`: Add metadata to the file.
- `--embed-thumbnail`: Add thumbnail to the file.
- `--write-subs`: Write subtitle file.
- `--sub-langs <lang>`: Languages of the subtitles to download.
- `-o <template>`: Output filename template (e.g., `%(title)s.%(ext)s`).
- `--flat-playlist`: Do not extract the videos of a playlist, only list them.
- `--dump-json`: Print JSON information about the video/playlist.

## Dependencies
- `yt-dlp`: Main YouTube downloader.
- `svtplay-dl`: Downloader for SVT Play and other Swedish sites.
- `ffmpeg`: Required for merging video/audio and subtitles.
- `mpv`: Media player for streaming.
- `gum`: TUI utility for interactive scripts.
