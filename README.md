# QuickTube

**QuickTube** is a powerful, terminal-based (TUI) media companion. It acts as a smart wrapper around `yt-dlp`, `mpv`, and `svtplay-dl`, giving you a fast and beautiful interface to stream or download videos directly from your terminal.

![QuickTube Menu](https://raw.githubusercontent.com/wulffern/QuickTube/main/img/QuickTube.gif)
*(Note: Screenshot may refer to an older version. New UI is even cleaner!)*

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

The python dependencies are listed in `requirements.txt`.

## 🚀 Installation & Usage

### Option 1: Run with `uv` (Recommended)
If you have [uv](https://github.com/astral-sh/uv) installed, you can run the project instantly without manual setup:

```bash
cd QuickTube
uv run main.py
```

### Option 2: Manual Setup
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

### Option 3: Build Standalone Executable
You can bundle the application into a single executable file using the included script (requires PyInstaller):

```bash
./build.sh
```
The executable will be placed in `dist/quicktube`.

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
