# QuickTube

**QuickTube** is a powerful, terminal-based (TUI) media companion. It acts as a smart wrapper around `yt-dlp`, `mpv`, and `svtplay-dl`, giving you a fast and beautiful interface to stream or download videos directly from your terminal.

![QuickTube Menu](https://raw.githubusercontent.com/wulffern/QuickTube/main/img/QuickTube.gif)
*(Note: Screenshot may refer to an older version. New UI is even cleaner!)*

## ⚠️ Compatibility Note

**This version has been primarily tested on Linux.**

While the code is written in Python and should technically run on other platforms, it has **not yet been verified on macOS or Windows**.
*   **macOS & Windows:** Support is experimental. Dedicated build scripts (`.bat` / `.sh`) and testing for these platforms are planned for a future update.

## ✨ Features

*   **📺 Stream & Download:** Instantly stream video/audio via `mpv` or download in best quality using `yt-dlp`.
*   **🧩 Smart Clipboard:** Automatically detects YouTube or SVT Play links in your clipboard upon startup.
*   **📜 History:** Keeps track of your 3 most recently accessed videos for quick re-access.
*   **⏯️ Playlist Support:** Detects playlists and offers to stream/download the whole set.
*   **🇸🇪 SVT Play Support:** Dedicated support for `svtplay.se` including series downloading and subtitles.
*   **🚀 Native TUI:** Built with Python using **Rich** and **InquirerPy** for a snappy, beautiful, and flicker-free experience.
*   **🍪 Browser Cookies:** Option to borrow cookies from your browser to bypass "Bot" or "Login" restrictions on YouTube.

## 🛠️ Requirements

*   **Python 3.10+**
*   **FFmpeg** (For merging video/audio)
*   **MPV** (For streaming)

## 🚀 Installation & Usage

### 1. Build Standalone Executable (Recommended)
The easiest way to run QuickTube is to build it into a single file. This requires `PyInstaller` (installed via the script).

```bash
./build.sh
```
The resulting executable will be placed in `dist/quicktube`. You can move this file anywhere (e.g., `/usr/local/bin`) and run it without needing Python installed.

### 2. Manual Setup (Virtual Environment)
If you prefer running the Python script directly:

1.  Clone the repository.
2.  Create a virtual environment and install dependencies:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```
3.  Run the app:
    ```bash
    python main.py
    ```

### 3. For Developers (Using `uv`)
If you are modifying the code or testing changes, `uv` is the fastest way to run the project without manually managing virtual environments to see results instantly:

```bash
uv run main.py
```

## ⚙️ Configuration & Data

QuickTube stores your history and logs in your system's standard configuration directory:
*   **Linux:** `~/.config/QuickTube/`
*   **macOS:** `~/Library/Application Support/QuickTube/`
*   **Windows:** `%APPDATA%\QuickTube\`

## 🏗️ Architecture

The project has recently been refactored from a monolithic script into a modular Python application:

*   `src/core.py` - Main logic for handling media interactions.
*   `src/ui.py` - TUI rendering using Rich and InquirerPy.
*   `src/history.py` - JSON-based persistence layer.
*   `src/config.py` - Path and resource management.

## 🤝 Contributing

Contributions are welcome! Please ensure any new features maintain the modular structure and TUI consistency.

## 📜 License

This project is intended for educational purposes. Please respect content creators and copyright laws when downloading media.