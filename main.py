#!/usr/bin/env python3
import sys
import os
import platform
from datetime import datetime

# Fix Windows console encoding to display emojis and gum-borders correctly
if platform.system() == "Windows":
    os.system("chcp 65001 > nul")
    # Force Python to use UTF-8 for stdout/stderr
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Add the current directory to sys.path to ensure src can be imported
# This helps if running from a different directory
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

from src.config import setup_resources, check_dependencies
from src.utils import write_log
from src.clipboard import get_clipboard
from src.ui import gum_input, gum_choose
from src.core import handle_svtplay, handle_youtube, select_cookie_browser, update_tools, is_valid_url
from src.history import load_history

def main():
    # Setup PATH to include bundled or local tools
    setup_resources()
    
    # Ensure dependencies exist
    check_dependencies()
    
    last_action = ""

    while True:
        clipboard_content = get_clipboard()
        url_from_clipboard = ""

        # Pre-fill only if last action was NOT stream
        if last_action != "stream":
            cleaned = clipboard_content.strip()
            if is_valid_url(cleaned):
                url_from_clipboard = cleaned
        
        last_action = ""

        # Input Prompt
        url = gum_input("Paste/type a URL (leave empty for menu)...", value=url_from_clipboard)

        # Handle explicit Cancel (Escape) or Empty input (Enter)
        if url is None:
             url = "" 

        if not url:
            # Main Menu logic
            history = load_history()
            
            menu_choices = [
                Choice(value="Paste link", name="Paste link"),
                Choice(value="Update tools", name="Update tools"),
                Choice(value="Select cookie browser", name="Select cookie browser")
            ]
            
            if history:
                menu_choices.append(Choice(value=None, name="Recent History", enabled=False))
                for item in history:
                    title = item.get("title", "Unknown")
                    h_url = item.get("url", "")
                    # Limit title length for UI
                    display_title = (title[:40] + '..') if len(title) > 40 else title
                    menu_choices.append(Choice(value=h_url, name=f"   {display_title}"))
            
            menu_choices.append(Choice(value="Exit", name="Exit"))

            choice = gum_choose(menu_choices, header="QuickTube\nMain Menu")
            
            if choice is None: # 'q' or 'esc' in main menu -> Exit
                break

            if choice == "Update tools":
                update_tools()
                continue
            elif choice == "Select cookie browser":
                select_cookie_browser()
                continue
            elif choice == "Exit":
                break
            elif choice == "Paste link":
                continue
            else:
                # If it's none of the above, it must be a URL from history
                url = choice

        is_svt = "svtplay.se" in url
        
        if is_svt:
            last_action = handle_svtplay(url)
        else:
            last_action = handle_youtube(url)

        print("")
        next_step = gum_choose(["New link", "Update tools", "Select cookie browser", "Exit"])
        
        if next_step is None: # Back pressed at end-screen -> Exit
            break

        if next_step == "Update tools":
            update_tools()
        elif next_step == "Select cookie browser":
            select_cookie_browser()
        elif next_step != "New link":
            break

if __name__ == "__main__":
    try:
        # Start log session
        try:
            log_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n--- NEW SESSION STARTED: {datetime.now()} ---\\n")
        except:
            pass

        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        write_log(f"CRITICAL ERROR: {e}")
        input("Press Enter to exit...")
