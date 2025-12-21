# QuickTube Build Instructions (Python)

This project can be built into a standalone executable for both Linux and macOS. The final binary includes all necessary tools (`yt-dlp`, `svtplay-dl`, `gum`) embedded within it.

## Prerequisites
You need to have **Python 3** installed on the system you are building on.

## Build for macOS
To build a binary for Mac, you must build it **on a Mac**.

1.  Copy the entire `quicktube-py-dist` folder to your Mac.
2.  Open Terminal and navigate to the folder:
    ```bash
    cd path/to/quicktube-py-dist
    ```
3.  Make the build script executable:
    ```bash
    chmod +x build_mac.sh
    ```
4.  Run the build script:
    ```bash
    ./build_mac.sh
    ```
    *The script will automatically download the correct versions of the tools for macOS and create the executable.*

5.  Your finished app is now in the `dist/` folder and is named `quicktube-mac`.

## Build for Linux
1.  Navigate to the folder in the terminal:
    ```bash
    cd quicktube-py-dist
    ```
2.  Make the build script executable:
    ```bash
    chmod +x build_linux.sh
    ```
3.  Run the build script:
    ```bash
    ./build_linux.sh
    ```
4.  Your finished binary is located in `dist/quicktube`.

## Notes
- **FFmpeg & MPV:** These programs are *not* included in the executable because they are very large. The user is expected to have these installed on their system (`brew install ffmpeg mpv` on Mac, `apt install ffmpeg mpv` on Linux).
