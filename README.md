# QuickTube

**A modern, terminal-based video downloader and streamer for YouTube and SVT Play.**

QuickTube is a robust CLI tool that simplifies interacting with media links. It acts as an interactive wrapper around industry-standard tools like `yt-dlp`, `mpv`, and `svtplay-dl`.

Built with **Python**, **Rich**, and **InquirerPy** for a beautiful and responsive terminal experience.

---

## 🚀 Features

*   **Smart Clipboard:** Automatically detects URLs when you start the program.
*   **Interactive Quality Selector:** Choose exactly which resolution and format you want via a sorted table.
*   **Streaming:** Watch videos instantly in `mpv` without waiting for downloads.
*   **SVT Play Support:** 
    *   Download full series or specific episodes.
    *   Embed subtitles automatically.
*   **Advanced YouTube Support:**
    *   **Cookie "Borrowing":** Use cookies from your browser (Chrome, Firefox, Brave, etc.) to bypass age restrictions or throttle.
    *   **Playlist Handling:** Download or stream entire playlists effortlessly.
    *   **Metadata Embedding:** Adds thumbnails and metadata to downloaded files.

---

## 🛠️ Prerequisites

### Required External Tools
Ensure these are installed and in your PATH:
*   **[mpv](https://mpv.io/)**: Essential for streaming playback.
*   **[ffmpeg](https://ffmpeg.org/)**: Required for merging high-quality video/audio streams.

### Auto-Managed Tools
QuickTube can automatically download and update these binaries for you:
*   **yt-dlp**
*   **svtplay-dl**

---

## 📥 Installation

**Prebuilt binary (Linux x86_64):** download `quicktube` from the [latest release](https://github.com/coffe/QuickTube/releases/latest), then `chmod +x quicktube` and run it. You still need `mpv` and `ffmpeg`.

**From source:**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/coffe/QuickTube.git
    cd QuickTube
    ```

2.  **Set up a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🎮 Usage

Run the program:
```bash
python quicktube.py
```

### Workflow
1.  **Copy a link** (YouTube or SVT Play) to your clipboard.
2.  **Run QuickTube.** It will ask if you want to use the detected link.
3.  **Select Action:** Stream, Download Video, or Download Audio.
4.  **Enjoy!**

### Controls
*   **Arrow Keys:** Navigate menus.
*   **Enter:** Confirm selection.
*   **Esc:** Go back / Cancel.
*   **Type:** Filter lists (where applicable).

---

## ⚙️ Configuration

*   **Config Location:** `~/.config/quicktube/config.json`
*   **Browser Cookies:** You can select which browser to borrow cookies from inside the application (Main Menu -> Select cookie browser).

---

## 📄 License
QuickTube is free software under the [GNU General Public License v3.0 or later](LICENSE).

**⚠️ Disclaimer:** This tool is for personal use and archiving. Please respect the Terms of Service of the content platforms and copyright laws.
