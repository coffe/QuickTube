# QuickTube 2.0 Suite

**A comprehensive terminal-based toolkit for YouTube and SVT Play.**

QuickTube 2.0 combines two powerful TUI (Terminal User Interface) tools into a single suite:
1.  **QuickTube:** A versatile video downloader and streamer.
2.  **YTRSS:** A minimalist, distraction-free YouTube RSS client.

Both tools are built with Python and feature modern, interactive interfaces.

---

## 🚀 Components

### 1. QuickTube (`quicktube.py`)
*The Swiss Army Knife for video links.*

*   **Stream & Download:** Instantly stream via `mpv` or download videos/audio using `yt-dlp`.
*   **SVT Play Support:** Download full series, specific episodes, or stream directly.
*   **Smart Features:**
    *   **Clipboard Detection:** Automatically grabs links from your clipboard on startup.
    *   **Cookie "Borrowing":** Use cookies from your browser (Chrome, Firefox, etc.) to access age-restricted content.
    *   **Quality Selection:** Interactive menu to choose the best video/audio format.

### 2. YTRSS (`ytrss.py`)
*The "Algorithm-Free" Subscription Manager.*

*   **Distraction-Free:** Follow your favorite channels without the YouTube homepage.
*   **RSS-Based:** Fetches feeds asynchronously (blazing fast).
*   **Dashboard:** View new videos, "Watch Later" queue, and toggle Shorts visibility.
*   **Integration:** Select a video in YTRSS to instantly play or download it via QuickTube.
*   **Local Data:** Stores viewing history and subscriptions locally (`~/.config/ytrss/`).

---

## 🛠️ Prerequisites

### External Tools
Ensure these are installed and in your PATH:
*   **[mpv](https://mpv.io/)**: Essential for streaming.
*   **[ffmpeg](https://ffmpeg.org/)**: Required for merging video/audio streams.

*(Note: The `quicktube` tool has a built-in helper to download `yt-dlp` and `svtplay-dl` binaries if you don't want to install them system-wide via pip/package manager.)*

---

## 📥 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/coffe/QuickTube2.0.git
    cd QuickTube2.0
    ```

2.  **Set up a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    # .venv\Scripts\activate   # Windows
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🎮 How to Use

### Running QuickTube (Downloader)
```bash
python quicktube.py
```
*   **Tip:** Copy a URL to your clipboard before running for instant action.
*   **Controls:** Arrow keys to navigate, `Enter` to select, `Esc` to go back.

### Running YTRSS (Feed Reader)
```bash
python ytrss.py
```
*   **Navigation:** `↑`/`↓` to browse, `Type` to filter/search.
*   **Actions:** `Enter` on a video to Play (opens QuickTube), Add to Watch Later, etc.
*   **Shortcuts:**
    *   `[ R ]` Refresh feeds
    *   `[ S ]` Toggle Shorts
    *   `[ + ]` Add channel (via RSS URL)
    *   `[ M ]` Mark visible as seen

---

## ⚙️ Configuration

*   **QuickTube:**
    *   Updates tools to user's local bin directory.
    *   Detects browser cookies for authentication.
*   **YTRSS:**
    *   Config stored in `~/.config/ytrss/`.
    *   Feeds: `ytRss.opml` (Standard OPML format).
    *   Database: `ytrss.db` (SQLite).

---

## 📄 License
MIT

**⚠️ Disclaimer:** This project is for educational purposes. Please respect the Terms of Service of the respective platforms and copyright laws.