#!/usr/bin/env python3
import subprocess
import shutil
import sys
import os
import re
import json
import platform
import urllib.request
from datetime import datetime

# Third-party libraries for UI (replacing gum)
try:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice
    from rich.console import Console
    from rich.style import Style
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print("Error: Missing dependencies.")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

# Global Console
console = Console()

# Keybindings mapping 'q' and 'escape' to the internal 'interrupt' action
# This causes the prompt to raise KeyboardInterrupt, which we catch.
kb_select = {
    "interrupt": [{"key": "q"}, {"key": "escape"}]
}

kb_input_esc = {
    "interrupt": [{"key": "escape"}]
}

# Configuration
CONFIG_DIR = os.path.expanduser("~/.config/quicktube")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

COOKIE_BROWSER = None
FORCE_IPV4 = platform.system() == "Linux"
JS_ENGINE = None

def load_config():
    """Load configuration from JSON file."""
    global COOKIE_BROWSER
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                COOKIE_BROWSER = config.get("cookie_browser")
        except Exception as e:
            write_log(f"Failed to load config: {e}", log_to_console=False)

def save_config():
    """Save current configuration to JSON file."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        config = {
            "cookie_browser": COOKIE_BROWSER
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        write_log(f"Failed to save config: {e}", log_to_console=False)

def get_user_bin_dir():
    """Return the path to the user's local bin directory depending on OS."""
    system = platform.system()
    home = os.path.expanduser("~")
    
    if system == "Windows":
        return os.path.join(os.environ.get("APPDATA", home), "QuickTube", "bin")
    elif system == "Darwin": # macOS
        return os.path.join(home, "Library", "Application Support", "QuickTube", "bin")
    else: # Linux / other
        return os.path.join(home, ".local", "bin", "quicktube_tools")

def get_js_engine():
    """Find a supported JavaScript engine (Node, QuickJS, Deno).
    TODO: Add support for checking a bundled binary in the future.
    """
    # 1. Check for bundled engine (placeholder for future implementation)
    # bundled_path = os.path.join(get_user_bin_dir(), "js-engine")
    # if os.path.exists(bundled_path): return bundled_path

    # 2. Check system PATH
    for engine in ["node", "quickjs", "deno"]:
        if shutil.which(engine):
            return engine
    return None

# Initialize Config & Resources
load_config()
JS_ENGINE = get_js_engine()


def setup_resources():
    """Configure PATH to include binaries."""
    paths_to_add = []
    user_bin = get_user_bin_dir()
    paths_to_add.append(user_bin)
    
    if paths_to_add:
        os.environ["PATH"] = os.pathsep.join(paths_to_add) + os.pathsep + os.environ["PATH"]

setup_resources()

def write_log(msg, log_to_console=True):
    """Write message to log file and optionally to console."""
    try:
        log_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "log.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        clean_msg = str(msg)
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {clean_msg}\n")
    except Exception:
        pass 

    if log_to_console:
        console.print(msg)

# --- UI Helper functions (The New Way) ---

def ui_print(text, style="magenta", border=False):
    if border:
        console.print(Panel(text, style=style, expand=False))
    else:
        console.print(text, style=style)

def ui_input(message, default=""):
    # For text input, we only bind escape to quit (q is needed for typing)
    try:
        return inquirer.text(message=message, default=default, keybindings=kb_input_esc, qmark="", amark="").execute()
    except KeyboardInterrupt:
        return None

def ui_select(choices, message="Select an option:"):
    if not choices:
        return None
    # For selection, both q and escape work
    try:
        return inquirer.select(message=message, choices=choices, keybindings=kb_select, qmark="", amark="").execute()
    except KeyboardInterrupt:
        return None

def run_command(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True):
    """Run a command and return the result."""
    try:
        write_log(f"RUNNING COMMAND: {' '.join(cmd)}", log_to_console=False)
        result = subprocess.run(
            cmd, 
            stdout=stdout,
            stderr=stderr,
            text=text, 
            encoding='utf-8', 
            errors='replace',
            check=False
        )
        return result
    except FileNotFoundError:
        write_log(f"Command not found: {cmd[0]}", log_to_console=False)
        return None

# --- Core functions ---

def check_dependencies():
    missing_deps = []
    dependencies = ["yt-dlp", "svtplay-dl", "mpv", "ffmpeg"]
    
    for dep in dependencies:
        if not shutil.which(dep):
            missing_deps.append(dep)
    
    if missing_deps:
        ui_print("Warning: The following external dependencies are missing from PATH:", style="bold yellow", border=True)
        for dep in missing_deps:
            console.print(f"- {dep}", style="red")
        
        ui_print("Some features might not work.", style="dim")
        
        if "mpv" in missing_deps or "ffmpeg" in missing_deps:
             ui_print("Critical: 'mpv' and 'ffmpeg' are required for playback/merging.", style="bold red")

    # Check for JS Engine (Critical for YouTube throttling)
    if not JS_ENGINE:
        ui_print("Warning: No JavaScript engine found (node, quickjs, deno).", style="yellow")
        ui_print("YouTube downloads might be throttled or fail.", style="dim")


def get_clipboard():
    system = platform.system()
    if system == "Windows":
        try:
            cmd = ["powershell", "-command", "Get-Clipboard"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return res.stdout.strip()
        except:
            return ""
    elif shutil.which("wl-paste"):
        res = run_command(["wl-paste"])
        return res.stdout.strip().replace('\0', '')
    elif shutil.which("xclip"):
        res = run_command(["xclip", "-o", "-selection", "clipboard"])
        return res.stdout.strip().replace('\0', '')
    elif shutil.which("pbpaste"):
        res = run_command(["pbpaste"])
        return res.stdout.strip()
    return ""

def is_valid_url(text):
    patterns = [
        r"https?://(www\.)?youtube\.com/",
        r"https?://(www\.)?youtu\.be/",
        r"https?://(www\.)?svtplay\.se/"
    ]
    for pattern in patterns:
        if re.match(pattern, text):
            return True
    return False

def get_ytdlp_base_cmd():
    cmd = ["yt-dlp", "--no-warnings", "--force-overwrites", "--embed-metadata", "--embed-thumbnail"]
    
    # 1. Network Stability
    if FORCE_IPV4:
        cmd.append("--force-ipv4")
    
    # 2. JS Engine (Fixes throttling/signatures)
    if JS_ENGINE:
        cmd.extend(["--js-runtime", JS_ENGINE])

    # 3. Auth
    if COOKIE_BROWSER:
        cmd.extend(["--cookies-from-browser", COOKIE_BROWSER])
    
    return cmd

def get_mpv_cmd(url, audio_only=False):
    """Construct a robust MPV command with embedded yt-dlp options."""
    cmd = ["mpv", "--force-window"]
    if audio_only:
        cmd.append("--no-video")
    
    # Locate yt-dlp binary
    ytdlp_path = shutil.which("yt-dlp")
    if ytdlp_path:
        cmd.append(f"--script-opts=ytdl_hook-ytdl_path={ytdlp_path}")

    # Build raw options string (Comma separated key=value)
    # Important: Boolean flags like force-ipv4 must end with "=" (empty value)
    raw_opts = []
    
    if FORCE_IPV4:
        raw_opts.append("force-ipv4=")
    
    if JS_ENGINE:
        raw_opts.append(f"js-runtime={JS_ENGINE}")
    
    if COOKIE_BROWSER:
        raw_opts.append(f"cookies-from-browser={COOKIE_BROWSER}")
    
    if raw_opts:
        cmd.append(f"--ytdl-raw-options={','.join(raw_opts)}")

    cmd.append(url)
    return cmd

def select_cookie_browser():
    global COOKIE_BROWSER
    browsers = ["None (Default)", "chrome", "firefox", "brave", "edge", "safari", "opera", "vivaldi", "chromium"]
    
    # Pre-select current choice if possible
    default_idx = 0
    if COOKIE_BROWSER in browsers:
        default_idx = browsers.index(COOKIE_BROWSER)

    choice = ui_select(browsers, message="Select browser to borrow cookies from:")
    
    if choice and choice != "None (Default)":
        COOKIE_BROWSER = choice
        ui_print(f"Browser selected: {COOKIE_BROWSER}", style="green")
    else:
        COOKIE_BROWSER = None
        ui_print("Cookies disabled.", style="yellow")
    
    save_config()

def handle_svtplay(url):
    message = "SVT Play link detected. What do you want to do?"
    choices = [
        "Download (Best quality + Subtitles)",
        "Download Whole Series (-A)",
        "Download Whole Series (yt-dlp)",
        "Download Specific Episodes (yt-dlp)",
        "Download the LAST X episodes (svtplay-dl)",
        "Stream (MPV)",
        "Download audio only"
    ]
    
    action = ui_select(choices, message=message)
    if not action: return

    console.print("") 
    success = False

    if action == "Download (Best quality + Subtitles)":
        ui_print("Starting download from SVT Play...", style="cyan")
        res = subprocess.run(["svtplay-dl", "-S", "-M", url])
        success = (res.returncode == 0)

    elif action == "Download Whole Series (-A)":
        ui_print("Starting download of entire series...", style="cyan")
        res = subprocess.run(["svtplay-dl", "-S", "-M", "-A", url])
        success = (res.returncode == 0)

    elif action == "Download Whole Series (yt-dlp)":
        ui_print("Starting download of entire series with yt-dlp...", style="cyan")
        cmd = get_ytdlp_base_cmd()
        cmd.extend([
            "--embed-subs", "--write-subs", "--sub-langs", "all",
            "-o", "%(series)s/S%(season_number)02dE%(episode_number)02d - %(title)s.%(ext)s",
            url
        ])
        res = subprocess.run(cmd)
        success = (res.returncode == 0)

    elif action == "Download Specific Episodes (yt-dlp)":
        items = ui_input("Enter episodes (e.g. 1, 2-5, 10)...")
        if items:
            ui_print(f"Downloading episodes {items} with yt-dlp...", style="cyan")
            cmd = get_ytdlp_base_cmd()
            cmd.extend([
                "--embed-subs", "--write-subs", "--sub-langs", "all",
                "--playlist-items", items,
                "-o", "%(series)s/S%(season_number)02dE%(episode_number)02d - %(title)s.%(ext)s",
                url
            ])
            res = subprocess.run(cmd)
            success = (res.returncode == 0)
        else:
            return

    elif action == "Download the LAST X episodes (svtplay-dl)":
        count = ui_input("Number of episodes from the end (e.g. 5)...")
        if count.isdigit():
            ui_print(f"Downloading the last {count} episodes...", style="cyan")
            res = subprocess.run(["svtplay-dl", "-S", "-M", "-A", "--all-last", count, url])
            success = (res.returncode == 0)
        else:
            ui_print("Invalid number specified.", style="red")
            return

    elif action == "Stream (MPV)":
        subprocess.run(["mpv", "--no-terminal", url])
        return "stream"

    elif action == "Download audio only":
        ui_print("Downloading audio only...", style="cyan")
        res = subprocess.run(["svtplay-dl", "--only-audio", url])
        success = (res.returncode == 0)

    if success:
        ui_print("✔ Download complete.", style="bold green")
    else:
        ui_print("❌ Download failed.", style="bold red")
    
    return "download"

def handle_youtube(url):
    # Get info
    with console.status("[bold green]Fetching video info...") as status:
        info_cmd = ["yt-dlp", "--flat-playlist", "--dump-json", "--no-warnings"]
        if FORCE_IPV4: info_cmd.append("--force-ipv4")
        if JS_ENGINE: info_cmd.extend(["--js-runtime", JS_ENGINE])
        if COOKIE_BROWSER: info_cmd.extend(["--cookies-from-browser", COOKIE_BROWSER])
        info_cmd.append(url)
        res = run_command(info_cmd)
    
    if not res or res.returncode != 0:
        ui_print("Could not retrieve information for the URL.", style="red")
        if not COOKIE_BROWSER:
            ui_print("Tip: Try selecting a browser for cookies in the main menu.", style="yellow")
        return

    try:
        first_line = res.stdout.strip().split('\n')[0]
        info = json.loads(first_line)
    except json.JSONDecodeError:
        ui_print("Could not parse video information.", style="red")
        return

    title = info.get("title", "Unknown title")
    is_playlist = info.get("_type") == "playlist" or "list=" in url
    
    formatted_title = f"{title[:57]}..." if len(title) > 60 else title

    if is_playlist:
        message = f"Playlist detected: {formatted_title}"
        choices = [
            "Stream Full Playlist (Video)", 
            "Stream Full Playlist (Audio)",
            "Download Full Playlist (Video)", 
            "Download Full Playlist (Audio)"
        ]
        action = ui_select(choices, message=message)

        if action == "Stream Full Playlist (Video)":
            cmd = get_mpv_cmd(url, audio_only=False)
            subprocess.run(cmd)
            return "stream"
        elif action == "Stream Full Playlist (Audio)":
            cmd = get_mpv_cmd(url, audio_only=True)
            subprocess.run(cmd)
            return "stream"
        
        cmd = get_ytdlp_base_cmd()
        
        if action == "Download Full Playlist (Video)":
            ui_print("Starting download of full playlist (video)...", style="cyan")
            cmd.extend([
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "--merge-output-format", "mp4",
                "-o", "%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s",
                url
            ])
        elif action == "Download Full Playlist (Audio)":
            ui_print("Starting download of full playlist (audio)...", style="cyan")
            cmd.extend([
                "-f", "bestaudio/best", "-x", "--audio-format", "opus",
                "-o", "%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s",
                url
            ])
        
        subprocess.run(cmd)
        ui_print("✔ Playlist download complete.", style="bold green")
        return "download"

    else:
        # Single video
        message = f"Video: {formatted_title}"
        choices = ["Stream Video (MPV)", "Stream Audio (MPV)", "Download video", "Download audio"]
        action = ui_select(choices, message=message)

        if action == "Stream Video (MPV)":
            cmd = get_mpv_cmd(url, audio_only=False)
            subprocess.run(cmd)
            return "stream"
        elif action == "Stream Audio (MPV)":
            cmd = get_mpv_cmd(url, audio_only=True)
            subprocess.run(cmd)
            return "stream"

        elif action == "Download audio":
            ui_print("Starting audio download...", style="cyan")
            cmd = get_ytdlp_base_cmd()
            cmd.extend([
                "-f", "bestaudio/best", "-x", "--audio-format", "opus",
                "-o", "%(title)s.%(ext)s", url
            ])
            subprocess.run(cmd)
            ui_print("✔ Download complete.", style="bold green")
            return "download"

        elif action == "Download video":
            with console.status("[bold green]Fetching available formats...") as status:
                # Use get_ytdlp_base_cmd to ensure cookies/ipv4/js options are used for fetching JSON
                # We slice off the default flags that might conflict with -J or are redundant, 
                # but actually base_cmd has --no-warnings etc which are fine.
                # However, base_cmd has --embed-metadata etc which we don't want for -J.
                # So we manually construct the fetch command but using the globals.
                
                fmt_cmd = ["yt-dlp", "-J"]
                if FORCE_IPV4: fmt_cmd.append("--force-ipv4")
                if JS_ENGINE: fmt_cmd.extend(["--js-runtime", JS_ENGINE])
                if COOKIE_BROWSER: fmt_cmd.extend(["--cookies-from-browser", COOKIE_BROWSER])
                
                fmt_cmd.append(url)
                res_fmt = run_command(fmt_cmd)
            
            if not res_fmt: return
            
            try:
                video_data = json.loads(res_fmt.stdout)
                formats = video_data.get("formats", [])
            except:
                return

            # Format selection logic
            unique_resolutions = {} 
            for f in formats:
                if f.get("vcodec") == "none": continue
                height = f.get("height") or 0
                if height == 0: continue
                
                current_fps = f.get("fps") or 0
                current_size = f.get("filesize") or f.get("filesize_approx") or 0
                
                if height not in unique_resolutions:
                    unique_resolutions[height] = f
                else:
                    existing = unique_resolutions[height]
                    existing_fps = existing.get("fps") or 0
                    if current_fps > existing_fps:
                         unique_resolutions[height] = f
                    # Add more replacement logic here if needed (e.g. bitrate)

            table_rows = []
            has_audio_map = {}
            
            for height, f in unique_resolutions.items():
                f_id = f.get("format_id", "N/A")
                res = f"{f.get('width', 0)}x{height}"
                fps = f.get("fps") or 0
                ext = f.get("ext", "N/A")
                has_audio = f.get("acodec", "none") != "none"
                has_audio_map[f_id] = has_audio
                audio_mark = "YES" if has_audio else "NO "
                filesize = f.get("filesize") or f.get("filesize_approx")
                size_str = f"{filesize / (1024*1024):.1f}MiB" if filesize else "N/A"

                row_str = f"{f_id:<5} | {res:<9} | {fps:<4} | {ext:<4} | 🎵:{audio_mark} | {size_str}"
                table_rows.append({'str': row_str, 'height': height, 'value': f_id})

            table_rows.sort(key=lambda x: x['height'], reverse=True)
            
            choices = [Choice(value=r['value'], name=r['str']) for r in table_rows]
            
            format_code = ui_select(choices, message="Select Quality (ID | Resolution | FPS | Type | Audio | Size)")
            if not format_code: return

            ui_print("Starting video download...", style="cyan")
            
            final_format = format_code
            if not has_audio_map.get(format_code, False):
                final_format += "+bestaudio"
            
            cmd = ["yt-dlp", "--force-overwrites", "--embed-metadata", "--embed-thumbnail"]
            if COOKIE_BROWSER:
                cmd.extend(["--cookies-from-browser", COOKIE_BROWSER])
            
            cmd.extend([
                "-f", final_format, 
                "--merge-output-format", "mp4", 
                "-o", "%(title)s-%(height)sp.%(ext)s",
                url
            ])
            
            subprocess.run(cmd)
            ui_print("✔ Download complete.", style="bold green")
            return "download"

def update_tools():
    """Download latest versions of tools."""
    user_bin = get_user_bin_dir()
    
    print("")
    ui_print(f"Tools will be installed/updated in: {user_bin}", style="dim")
    
    choice = ui_select(["Yes, update", "Cancel"], message="Do you want to download the latest yt-dlp and svtplay-dl?")
    if choice != "Yes, update":
        return

    try:
        os.makedirs(user_bin, exist_ok=True)
    except OSError as e:
        ui_print(f"Could not create directory: {e}", style="red")
        return
    
    system = platform.system()
    
    # --- YT-DLP ---
    ytdlp_filename_remote = "yt-dlp"
    if system == "Windows": ytdlp_filename_remote = "yt-dlp.exe"
    elif system == "Darwin": ytdlp_filename_remote = "yt-dlp_macos"
    
    ytdlp_url = f"https://github.com/yt-dlp/yt-dlp/releases/latest/download/{ytdlp_filename_remote}"
    ytdlp_local = "yt-dlp.exe" if system == "Windows" else "yt-dlp"
    
    ui_print("Downloading latest yt-dlp...", style="cyan")
    try:
        urllib.request.urlretrieve(ytdlp_url, os.path.join(user_bin, ytdlp_local))
        if system != "Windows":
            os.chmod(os.path.join(user_bin, ytdlp_local), 0o755)
        ui_print("✔ yt-dlp updated.", style="green")
    except Exception as e:
        ui_print(f"❌ Failed to update yt-dlp: {e}", style="red")

    # --- SVTPLAY-DL ---
    if system != "Darwin":
        svt_remote = "svtplay-dl.exe" if system == "Windows" else "svtplay-dl"
        svt_url = f"https://github.com/spaam/svtplay-dl/releases/latest/download/{svt_remote}"
        
        ui_print("Downloading latest svtplay-dl...", style="cyan")
        try:
            urllib.request.urlretrieve(svt_url, os.path.join(user_bin, svt_remote))
            if system != "Windows":
                os.chmod(os.path.join(user_bin, svt_remote), 0o755)
            ui_print("✔ svtplay-dl updated.", style="green")
        except Exception as e:
            ui_print(f"❌ Failed to update svtplay-dl: {e}", style="red")
    else:
         ui_print("ℹ️  svtplay-dl update on Mac requires manual handling (zip).", style="dim")

    print("")
    ui_print("Done. Restart the program to use the new versions.", style="green")
    input("Press Enter to continue...")


def main():
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
        url = ""

        if url_from_clipboard:
            # Shorten for display
            display_url = (url_from_clipboard[:50] + '...') if len(url_from_clipboard) > 50 else url_from_clipboard
            
            choices = [
                Choice(value="use_clip", name=f"Use link: {display_url}"),
                Choice(value="new", name="Paste/Type another URL"),
                Choice(value="menu", name="Main Menu")
            ]
            
            action = ui_select(choices, message="Clipboard link detected:")
            
            if action is None: break # Quit
            
            if action == "use_clip":
                url = url_from_clipboard
            elif action == "new":
                url = ui_input("Paste/type a URL:")
                if url is None: break
            # if action == "menu", url remains empty -> triggers menu below
        else:
            url = ui_input("Paste/type a URL (leave empty for menu):")
            if url is None: break

        if not url:
            # Main Menu
            choice = ui_select(["Paste link", "Update tools", "Select cookie browser", "Exit"], message="Main Menu")
            
            if choice is None or choice == "Exit":
                break
            elif choice == "Update tools":
                update_tools()
                continue
            elif choice == "Select cookie browser":
                select_cookie_browser()
                continue
            elif choice == "Paste link":
                # Force input on next loop
                url = ui_input("Paste/type a URL:")
                if not url: continue

        is_svt = "svtplay.se" in url
        
        if is_svt:
            last_action = handle_svtplay(url)
        else:
            last_action = handle_youtube(url)

        print("")
        next_step = ui_select(["New link", "Update tools", "Select cookie browser", "Exit"])
        
        if next_step is None or next_step == "Exit":
            break
        elif next_step == "Update tools":
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
                f.write(f"\n\n--- NEW SESSION STARTED: {datetime.now()} ---\n")
        except:
            pass

        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        write_log(f"CRITICAL ERROR: {e}")
        input("Press Enter to exit...")
