from rich.console import Console
from rich.markdown import Markdown

def show_guide():
    console = Console()
    
    guide_text = """
# QuickTube Expert Guide

Welcome to the professional way of handling web media. Here is how you master QuickTube:

## 1. The Clipboard Flow
QuickTube is designed for speed. When you start the app, it immediately looks at your system clipboard. 
- **Tip:** Copy a YouTube or SVT Play link *before* you start the app, and you can just hit **Enter** to process it instantly.

## 2. Batch Downloading
Need to download 50 videos? Don't do it one by one.
- **Menu:** Use the 'Batch Download from file' option and select a `.txt` file with one URL per line.
- **CLI:** Run `quicktube links.txt` directly from your terminal to start a batch job immediately.

## 3. Bypassing Bot Detection
If you get "Sign in to confirm you are not a bot" errors:
- Use the **'Select cookie browser'** option in the main menu.
- Choose the browser where you are currently logged into YouTube (e.g., Chrome or Firefox).
- QuickTube will "borrow" your session cookies to authenticate the download.

## 4. Navigation Shortcuts
- **q / Esc:** Use these to go back or cancel at any time.
- **Up/Down/Enter:** Standard navigation.
- **q:** In the Main Menu, this exits the application.

## 5. Storage & Logs
- **Logs:** If something fails, check `log.txt` in the application folder.
- **History:** QuickTube remembers your last 3 videos. You can access them directly from the Main Menu.

---
*Press Enter to return to the menu*
"""
    console.clear()
    console.print(Markdown(guide_text))
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass
