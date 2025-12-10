# QuickTube - A YouTube TUI Helper

A simple TUI (Terminal User Interface) helper script to quickly stream or download YouTube videos and audio directly from your terminal. It uses `gum` to create a user-friendly menu, automatically detects a YouTube link in your clipboard, and lets you decide what to do with it.

![demo-gif](https://raw.githubusercontent.com/wulffern/QuickTube/main/img/QuickTube.gif)

## Features

- **Stream Video**: Instantly stream a video in `mpv`.
- **Stream Audio**: Listen to audio-only in `mpv`, perfect for podcasts or music.
- **Download Video**: Choose from a list of available video resolutions and download the best quality version, which is then merged with the best audio track into an MP4 file.
- **Download Audio**: Download the best audio available and convert it to the efficient `opus` format.
- **Playlist Support**: Automatically detects playlists and offers options to stream or download the entire list, with files named and numbered to preserve the correct order.
- **Clipboard Detection**: Automatically grabs a YouTube URL from your clipboard to speed up your workflow.
- **Interactive Menu**: A clean, interactive menu system powered by `gum`.

## Playlist Support

The script intelligently detects if the provided URL is a playlist (by checking for `list=` in the URL). When a playlist is detected, the menu adapts to offer playlist-specific actions:

- **Stream Full Playlist**: Open the entire playlist directly in `mpv` (video or audio-only).
- **Download Full Playlist**: 
    - Downloads all videos (or audio tracks) in the playlist.
    - Creates a subfolder named after the playlist.
    - Files are automatically numbered (e.g., `01 - Title.mp4`, `02 - Title.mp4`) to ensure they sort correctly according to the playlist order.
    - Video downloads automatically select the best MP4 quality.
    - Audio downloads are converted to `opus`.

## Scripts

This repository contains two versions of the script:

- **`yt-helper.v1.sh`**: The main script, intended for **Linux** users (using `wl-paste` or `xclip`).
- **`yt-helper-mac.sh`**: A specific version for **macOS** users (using `pbpaste`).

## Dependencies

Before running the script, make sure you have the following programs installed:

- **[gum](https://github.com/charmbracelet/gum)**: For the interactive menus.
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)**: For interacting with YouTube.
- **[mpv](https://mpv.io/)**: For streaming video and audio.
- **[ffmpeg](https://ffmpeg.org/)**: For merging video/audio and for audio conversion.

You will also need a clipboard tool:
- **For Linux**: `wl-paste` (for Wayland) or `xclip` (for X11).
- **For macOS**: `pbpaste` is included by default.

### Installation Example (Homebrew on macOS)
```bash
brew install gum yt-dlp mpv ffmpeg
```

### Installation Example (APT on Debian/Ubuntu)
```bash
sudo apt install gum yt-dlp mpv ffmpeg xclip
```

## How to Use

1. Make sure all dependencies are installed.
2. Make the script executable:
   ```bash
   # For Linux
   chmod +x yt-helper.v1.sh

   # For macOS
   chmod +x yt-helper-mac.sh
   ```
3. Run the script:
   ```bash
   # For Linux
   ./yt-helper.v1.sh

   # For macOS
   ./yt-helper-mac.sh
   ```
4. Paste a YouTube URL or let the script pick it up from your clipboard, and choose your desired action from the menu.

## Disclaimer

This script is created solely for educational purposes to demonstrate shell scripting and TUI creation with `gum`. It is **not** intended to be used for downloading copyrighted content without permission. Users are responsible for complying with YouTube's Terms of Service and all applicable copyright laws. Please respect content creators and their work.