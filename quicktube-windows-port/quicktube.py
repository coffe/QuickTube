#!/usr/bin/env python3
import subprocess
import shutil
import sys
import os
import re
import json
import csv
import io
import platform
import urllib.request
import tempfile
from datetime import datetime

# Fix Windows console encoding to display emojis and gum-borders correctly
if platform.system() == "Windows":
    os.system("chcp 65001 > nul")
    # Force Python to use UTF-8 for stdout/stderr
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

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

def setup_resources():
    """Configure PATH to include binaries."""
    paths_to_add = []
    
    # 1. User's updated binaries (highest priority)
    user_bin = get_user_bin_dir()
    paths_to_add.append(user_bin)
    
    # 2. Embedded binaries (PyInstaller)
    if hasattr(sys, '_MEIPASS'):
        bundle_bin = os.path.join(sys._MEIPASS, "bin")
        paths_to_add.append(bundle_bin)
    else:
        # Dev mode
        dev_bin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
        if os.path.exists(dev_bin):
            paths_to_add.append(dev_bin)
    
    # Add to PATH
    if paths_to_add:
        os.environ["PATH"] = os.pathsep.join(paths_to_add) + os.pathsep + os.environ["PATH"]

setup_resources()

# Global setting
COOKIE_BROWSER = None

def get_ytdlp_base_cmd():
    """Return base command for yt-dlp including cookies if selected."""
    cmd = ["yt-dlp", "--no-warnings", "--force-overwrites", "--embed-metadata", "--embed-thumbnail"]
    if COOKIE_BROWSER:
        cmd.extend(["--cookies-from-browser", COOKIE_BROWSER])
    return cmd

def select_cookie_browser():
    """Select browser for cookies."""
    global COOKIE_BROWSER
    
    browsers = ["None (Default)", "chrome", "firefox", "brave", "edge", "safari", "opera", "vivaldi", "chromium"]
    choice = gum_choose(browsers, header="Select browser to borrow cookies from (fixes 'Bot' errors):")
    
    if choice and choice != "None (Default)":
        COOKIE_BROWSER = choice
        gum_style(f"Browser selected: {COOKIE_BROWSER}", foreground="212")
    else:
        COOKIE_BROWSER = None
        gum_style("Cookies disabled.", foreground="212")

def write_log(msg, console=True):
    """Write message to log file and optionally to console."""
    try:
        log_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "log.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Strip ANSI codes for the log file
        ansi_escape = re.compile(r'\x1B(?:[@-Z\-_]|[[0-?]*[ -/]*[@-~])')
        clean_msg = ansi_escape.sub('', str(msg))
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {clean_msg}\n")
    except Exception:
        pass # Ignore log errors

    if console:
        print(msg)

# --- Helper functions for external commands (GUM wrappers) ---

def run_command(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True):
    """Run a command and return the result."""
    try:
        write_log(f"RUNNING COMMAND: {' '.join(cmd)}", console=False)
        
        # Force UTF-8 encoding for input/output
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
        write_log(f"Command not found: {cmd[0]}", console=False)
        return None

def gum_style(text, foreground=None, border=None, padding=None, border_foreground=None):
    """Wrapper for 'gum style'."""
    cmd = ["gum", "style"]
    if foreground:
        cmd.extend(["--foreground", foreground])
    if border:
        cmd.extend(["--border", border])
    if padding:
        cmd.extend(["--padding", padding])
    if border_foreground:
        cmd.extend(["--border-foreground", border_foreground])
    
    cmd.append(text)
    subprocess.run(cmd)

def gum_input(placeholder, value=""):
    """Wrapper for 'gum input'."""
    cmd = ["gum", "input", "--placeholder", placeholder]
    if value:
        cmd.extend(["--value", value])
    
    # stderr=None lets gum draw the UI to the terminal
    res = run_command(cmd, stderr=None)
    return res.stdout.strip() if res else ""

def gum_choose(choices, header=None):
    """Wrapper for 'gum choose'."""
    if header:
        print("") # Newline for aesthetics
        gum_style(header, border="rounded", padding="1 2", border_foreground="240")
    
    cmd = ["gum", "choose"] + choices
    # stderr=None lets gum draw the UI to the terminal
    res = run_command(cmd, stderr=None)
    return res.stdout.strip() if res else ""

def gum_table(csv_data, header):
    """Wrapper for 'gum table'."""
    full_data = header + "\n" + csv_data
    
    # Create temp file for CSV data to avoid pipe deadlock
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', suffix='.csv') as tf:
        tf.write(full_data)
        tf_path = tf.name
    
    try:
        # Read from file instead of pipe
        with open(tf_path, 'r', encoding='utf-8') as f:
            process = subprocess.run(
                ["gum", "table", "-s", ",", "--height", "10"],
                stdin=f,
                stdout=subprocess.PIPE,
                stderr=None, 
                text=True,
                encoding='utf-8'
            )
            return process.stdout.strip()
    finally:
        if os.path.exists(tf_path):
            try:
                os.remove(tf_path)
            except:
                pass

# --- Core functions ---

def check_dependencies():
    missing_deps = []
    # mpv and ffmpeg are expected on the system, gum/yt-dlp/svtplay-dl are bundled or in bin
    dependencies = ["gum", "yt-dlp", "svtplay-dl", "mpv", "ffmpeg"]
    
    for dep in dependencies:
        if not shutil.which(dep):
            missing_deps.append(dep)
    
    # Check clipboard only on Linux
    if platform.system() == "Linux":
        if not shutil.which("wl-paste") and not shutil.which("xclip"):
            missing_deps.append("wl-paste or xclip")
        
    if missing_deps:
        gum_style("Error: The following dependencies are missing:", foreground="212")
        for dep in missing_deps:
            print(f"- {dep}")
        gum_style("Please install them and try again.", foreground="212")
        sys.exit(1)

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
    """Simple check if the text looks like a relevant URL."""
    patterns = [
        r"https?://(www\.)?youtube\.com/",
        r"https?://(www\.)?youtu\.be/",
        r"https?://(www\.)?svtplay\.se/"
    ]
    for pattern in patterns:
        if re.match(pattern, text):
            return True
    return False

# --- Main Logic ---

def handle_svtplay(url):
    header_text = "SVT Play link detected.\nWhat do you want to do?"
    choices = [
        "Download (Best quality + Subtitles)",
        "Download Whole Series (-A)",
        "Download Whole Series (yt-dlp)",
        "Download Specific Episodes (yt-dlp)",
        "Download the LAST X episodes (svtplay-dl)",
        "Stream (MPV)",
        "Download audio only"
    ]
    
    action = gum_choose(choices, header=header_text)
    
    if not action: return

    print("") # Spacer
    success = False

    if action == "Download (Best quality + Subtitles)":
        gum_style("Starting download from SVT Play...")
        res = subprocess.run(["svtplay-dl", "-S", "-M", url])
        success = (res.returncode == 0)

    elif action == "Download Whole Series (-A)":
        gum_style("Starting download of entire series...")
        res = subprocess.run(["svtplay-dl", "-S", "-M", "-A", url])
        success = (res.returncode == 0)

    elif action == "Download Whole Series (yt-dlp)":
        gum_style("Starting download of entire series with yt-dlp...")
        cmd = get_ytdlp_base_cmd()
        cmd.extend([
            "--embed-subs", "--write-subs", "--sub-langs", "all",
            "-o", "%(series)s/S%(season_number)02dE%(episode_number)02d - %(title)s.%(ext)s",
            url
        ])
        res = subprocess.run(cmd)
        success = (res.returncode == 0)

    elif action == "Download Specific Episodes (yt-dlp)":
        items = gum_input("Enter episodes (e.g. 1, 2-5, 10)...")
        if items:
            gum_style(f"Downloading episodes {items} with yt-dlp...")
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
        count = gum_input("Number of episodes from the end (e.g. 5)...")
        if count.isdigit():
            gum_style(f"Downloading the last {count} episodes...")
            res = subprocess.run(["svtplay-dl", "-S", "-M", "-A", "--all-last", count, url])
            success = (res.returncode == 0)
        else:
            gum_style("Invalid number specified.", foreground="196")
            return

    elif action == "Stream (MPV)":
        subprocess.run(["mpv", "--no-terminal", url])
        return "stream"

    elif action == "Download audio only":
        gum_style("Downloading audio only...")
        res = subprocess.run(["svtplay-dl", "--only-audio", url])
        success = (res.returncode == 0)

    # Result message
    print("")
    if success:
        gum_style("✔ Download complete.", foreground="212")
    else:
        gum_style("❌ Download failed.", foreground="196")
    
    return "download"

def handle_youtube(url):
    # Get info as JSON
    info_cmd = ["yt-dlp", "--flat-playlist", "--dump-json", "--no-warnings"]
    if COOKIE_BROWSER: info_cmd.extend(["--cookies-from-browser", COOKIE_BROWSER])
    info_cmd.append(url)
    
    res = run_command(info_cmd)
    
    if not res or res.returncode != 0:
        gum_style("Could not retrieve information for the URL.", foreground="212")
        if res:
            print(f"\n--- DEBUG INFO ---")
            print(f"Command: {' '.join(info_cmd)}")
            print(f"Return code: {res.returncode}")
            print(f"Error output:\n{res.stderr}")
            print(f"------------------\n")
        
        if not COOKIE_BROWSER:
            gum_style("Tip: Try selecting a browser for cookies in the main menu.", foreground="240")
        return

    try:
        first_line = res.stdout.strip().split('\n')[0]
        info = json.loads(first_line)
    except json.JSONDecodeError:
        gum_style("Could not parse video information.", foreground="212")
        return

    title = info.get("title", "Unknown title")
    is_playlist = info.get("_type") == "playlist" or "list=" in url
    
    formatted_title = f"{title[:57]}..." if len(title) > 60 else title

    if is_playlist:
        header = f"What do you want to do with the playlist:\n{formatted_title}?"
        choices = [
            "Stream Full Playlist (Video)", 
            "Stream Full Playlist (Audio)",
            "Download Full Playlist (Video)", 
            "Download Full Playlist (Audio)"
        ]
        action = gum_choose(choices, header=header)

        if action == "Stream Full Playlist (Video)":
            subprocess.run(["mpv", "--no-terminal", url])
            return "stream"
        elif action == "Stream Full Playlist (Audio)":
            subprocess.run(["mpv", "--no-video", url])
            return "stream"
        
        # For download
        print("")
        cmd = get_ytdlp_base_cmd()
        
        if action == "Download Full Playlist (Video)":
            gum_style("Starting download of full playlist (video)...")
            cmd.extend([
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "--merge-output-format", "mp4",
                "-o", "%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s",
                url
            ])
        elif action == "Download Full Playlist (Audio)":
            gum_style("Starting download of full playlist (audio)...")
            cmd.extend([
                "-f", "bestaudio/best", "-x", "--audio-format", "opus",
                "-o", "%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s",
                url
            ])
        
        subprocess.run(cmd)
        gum_style("✔ Playlist download complete.", foreground="212")
        return "download"

    else:
        # Single video
        header = f"What do you want to do with:\n{formatted_title}?"
        choices = ["Stream Video (MPV)", "Stream Audio (MPV)", "Download video", "Download audio"]
        action = gum_choose(choices, header=header)

        if action == "Stream Video (MPV)":
            subprocess.run(["mpv", "--no-terminal", url])
            return "stream"
        elif action == "Stream Audio (MPV)":
            subprocess.run(["mpv", "--no-video", url])
            return "stream"

        elif action == "Download audio":
            print("")
            gum_style("Starting audio download...")
            cmd = get_ytdlp_base_cmd()
            cmd.extend([
                "-f", "bestaudio/best", "-x", "--audio-format", "opus",
                "-o", "%(title)s.%(ext)s", url
            ])
            subprocess.run(cmd)
            gum_style("✔ Download complete.", foreground="212")
            return "download"

        elif action == "Download video":
            fmt_cmd = ["yt-dlp", "-J"]
            if COOKIE_BROWSER: fmt_cmd.extend(["--cookies-from-browser", COOKIE_BROWSER])
            fmt_cmd.append(url)
            
            res_fmt = run_command(fmt_cmd)
            if not res_fmt: return
            
            try:
                video_data = json.loads(res_fmt.stdout)
                formats = video_data.get("formats", [])
            except:
                return

            table_rows = []
            has_audio_map = {}
            
            # Group formats by height to show only ONE choice per resolution (the best one)
            unique_resolutions = {} # Key: height (int), Value: format_dict

            for f in formats:
                if f.get("vcodec") == "none": continue
                
                height = f.get("height") or 0
                width = f.get("width") or 0
                
                if height == 0: continue

                current_size = f.get("filesize") or f.get("filesize_approx") or 0
                current_tbr = f.get("tbr") or f.get("vbr") or 0
                current_fps = f.get("fps") or 0
                
                if height not in unique_resolutions:
                    unique_resolutions[height] = f
                else:
                    existing = unique_resolutions[height]
                    existing_size = existing.get("filesize") or existing.get("filesize_approx") or 0
                    existing_tbr = existing.get("tbr") or existing.get("vbr") or 0
                    existing_fps = existing.get("fps") or 0
                    
                    replace = False
                    
                    if current_fps > existing_fps:
                        replace = True
                    elif current_fps < existing_fps:
                        replace = False
                    else:
                        if current_size > 0 and existing_size > 0:
                            if current_size > existing_size: replace = True
                        elif current_tbr > 0 and existing_tbr > 0:
                            if current_tbr > existing_tbr: replace = True
                        elif current_size > 0 and existing_size == 0:
                            replace = True
                        elif current_tbr > 0 and existing_tbr == 0:
                             replace = True
                    
                    if replace:
                        unique_resolutions[height] = f

            for height, f in unique_resolutions.items():
                f_id = f.get("format_id", "N/A")
                width = f.get("width") or 0
                res = f"{width}x{height}"
                fps = f.get("fps") or 0
                ext = f.get("ext", "N/A")
                
                acodec = f.get("acodec", "none")
                has_audio = acodec != "none"
                has_audio_map[f_id] = has_audio
                audio_mark = "YES" if has_audio else "NO "

                filesize = f.get("filesize") or f.get("filesize_approx")
                size_str = "N/A"
                if filesize:
                    size_str = f"{filesize / (1024*1024):.1f}MiB"

                row_str = f"{f_id:<5} | {res:<9} | {fps:<4} | {ext:<4} | 🎵:{audio_mark} | {size_str}"
                
                table_rows.append({'str': row_str, 'height': height, 'fps': fps})

            table_rows.sort(key=lambda x: x['height'], reverse=True)
            
            choices = [r['str'] for r in table_rows]

            header = "Select Quality (ID | Resolution | FPS | Type | Audio | Size)"
            choice = gum_choose(choices, header=header)
            
            if not choice: return

            format_code = choice.split('|')[0].strip()
            print("")
            gum_style("Starting video download...")
            
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
            gum_style("✔ Download complete (or finished).", foreground="212")
            return "download"


def update_tools():
    """Download latest versions of tools."""
    user_bin = get_user_bin_dir()
    
    print("")
    gum_style(f"Tools will be installed/updated in: {user_bin}", foreground="240")
    
    if gum_choose(["Yes, update", "Cancel"], header="Do you want to download the latest yt-dlp and svtplay-dl?") != "Yes, update":
        return

    try:
        os.makedirs(user_bin, exist_ok=True)
    except OSError as e:
        gum_style(f"Could not create directory: {e}", foreground="196")
        return
    
    system = platform.system()
    
    # --- YT-DLP ---
    ytdlp_filename_remote = "yt-dlp"
    if system == "Windows": ytdlp_filename_remote = "yt-dlp.exe"
    elif system == "Darwin": ytdlp_filename_remote = "yt-dlp_macos"
    
    ytdlp_url = f"https://github.com/yt-dlp/yt-dlp/releases/latest/download/{ytdlp_filename_remote}"
    ytdlp_local = "yt-dlp.exe" if system == "Windows" else "yt-dlp"
    
    gum_style("Downloading latest yt-dlp...", foreground="212")
    try:
        urllib.request.urlretrieve(ytdlp_url, os.path.join(user_bin, ytdlp_local))
        if system != "Windows":
            os.chmod(os.path.join(user_bin, ytdlp_local), 0o755)
        gum_style("✔ yt-dlp updated.", foreground="212")
    except Exception as e:
        gum_style(f"❌ Failed to update yt-dlp: {e}", foreground="196")

    # --- SVTPLAY-DL ---
    if system != "Darwin":
        svt_remote = "svtplay-dl.exe" if system == "Windows" else "svtplay-dl"
        svt_url = f"https://github.com/spaam/svtplay-dl/releases/latest/download/{svt_remote}"
        
        gum_style("Downloading latest svtplay-dl...", foreground="212")
        try:
            urllib.request.urlretrieve(svt_url, os.path.join(user_bin, svt_remote))
            if system != "Windows":
                os.chmod(os.path.join(user_bin, svt_remote), 0o755)
            gum_style("✔ svtplay-dl updated.", foreground="212")
        except Exception as e:
            gum_style(f"❌ Failed to update svtplay-dl: {e}", foreground="196")
    else:
         gum_style("ℹ️  svtplay-dl update on Mac requires manual handling (zip).", foreground="240")

    print("")
    gum_style("Done. Restart the program to use the new versions.", foreground="212")
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

        url = gum_input("Paste/type a URL (leave empty for menu)...", value=url_from_clipboard)

        if not url:
            # Main Menu
            choice = gum_choose(["Paste link", "Update tools", "Select cookie browser", "Exit"], header="Main Menu")
            
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

        is_svt = "svtplay.se" in url
        
        if is_svt:
            last_action = handle_svtplay(url)
        else:
            last_action = handle_youtube(url)

        print("")
        next_step = gum_choose(["New link", "Update tools", "Select cookie browser", "Exit"])
        
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