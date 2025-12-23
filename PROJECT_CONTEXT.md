# QuickTube 2.0 Project Context

## Overview
This project combines two Python-based CLI tools designed for a terminal-centric YouTube and SVT Play experience. It appears to be a merger of "QuickTube" (video downloader/streamer) and "YTRSS" (YouTube RSS feed reader).

## Core Components

### 1. QuickTube (`quicktube.py`)
A direct interaction tool for processing specific video URLs.
- **Functionality:**
  - Detects URLs from the clipboard automatically.
  - **YouTube:** Downloads video/audio (selectable quality), streams via `mpv`, downloads playlists.
  - **SVT Play:** Downloads episodes, series, or streams via `mpv`.
  - **Dependencies:** Wraps `yt-dlp` and `svtplay-dl`.
- **UI:** Interactive menu using `InquirerPy` and `rich`.

### 2. YTRSS (`ytrss.py`)
A "subscription manager" to follow YouTube channels without using the website.
- **Functionality:**
  - Fetches RSS feeds for YouTube channels asynchronously.
  - **Database:** Uses SQLite (`~/.config/ytrss/ytrss.db`) to track "seen" videos and metadata.
  - **Config:** Stores subscriptions in an OPML file (`~/.config/ytrss/ytRss.opml`).
  - **Features:** "Watch Later" playlist, filtering "Shorts", dashboard view.
  - **Integration:** Calls `quicktube` to play selected videos.

## Project Structure
- `quicktube.py`: Main entry point for single-link operations.
- `ytrss.py`: Main entry point for the RSS reader interface.
- `requirements.txt`: Python dependencies.
- `build.sh`: Script to likely bundle the application (possibly using PyInstaller, implied by `dist/` folder presence).

## Current Status & Issues
- **Merge Conflicts:**
  - `requirements.txt` contains conflict markers (`<<<<<<< HEAD`), showing a collision between `ytrss` dependencies (`feedparser`, `aiohttp`) and `quicktube` dependencies (`yt-dlp`, `svtplay-dl`).
  - `README.md` also contains conflict markers, with two different descriptions for the project.
