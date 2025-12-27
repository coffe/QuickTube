import os
import sys
import re
import json
import subprocess
import urllib.request
import platform
from pathlib import Path

from src.utils import run_command, write_log
from src.ui import gum_style, gum_choose, gum_input, gum_table
import src.config as config
from src.history import add_to_history

def get_ytdlp_base_cmd():
    """Return base command for yt-dlp including cookies if selected."""
    cmd = ["yt-dlp", "--no-warnings", "--embed-metadata", "--embed-thumbnail"]
    if config.COOKIE_BROWSER:
        cmd.extend(["--cookies-from-browser", config.COOKIE_BROWSER])
    return cmd

def select_cookie_browser():
    """Select browser for cookies."""
    browsers = ["None (Default)", "chrome", "firefox", "brave", "edge", "safari", "opera", "vivaldi", "chromium"]
    choice = gum_choose(browsers, header="Select browser to borrow cookies from (fixes 'Bot' errors):")
    
    if choice is None: return

    if choice and choice != "None (Default)":
        config.COOKIE_BROWSER = choice
        gum_style(f"Browser selected: {config.COOKIE_BROWSER}", foreground="212")
    else:
        config.COOKIE_BROWSER = None
        gum_style("Cookies disabled.", foreground="212")

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

def handle_svtplay(url):
    # SVT Play logic doesn't fetch title upfront to keep it fast, so we use URL as title
    add_to_history(url, url)

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

    print("\n") # Spacer
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
        if items is None: return # Back pressed

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
        if count is None: return # Back pressed

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
    print("\n")
    if success:
        gum_style("✔ Download complete.", foreground="212")
    else:
        gum_style("❌ Download failed.", foreground="196")
    
    return "download"

def handle_youtube(url):
    # Get info as JSON
    info_cmd = ["yt-dlp", "--flat-playlist", "--dump-json", "--no-warnings"]
    if config.COOKIE_BROWSER: info_cmd.extend(["--cookies-from-browser", config.COOKIE_BROWSER])
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
        
        if not config.COOKIE_BROWSER:
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
    
    # Save to history
    add_to_history(title, url)
    
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
        
        if action is None: return

        if action == "Stream Full Playlist (Video)":
            subprocess.run(["mpv", "--no-terminal", url])
            return "stream"
        elif action == "Stream Full Playlist (Audio)":
            subprocess.run(["mpv", "--no-video", url])
            return "stream"
        
        # For download
        print("\n")
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
        
        if action is None: return

        if action == "Stream Video (MPV)":
            subprocess.run(["mpv", "--no-terminal", url])
            return "stream"
        elif action == "Stream Audio (MPV)":
            subprocess.run(["mpv", "--no-video", url])
            return "stream"

        elif action == "Download audio":
            print("\n")
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
            if config.COOKIE_BROWSER: fmt_cmd.extend(["--cookies-from-browser", config.COOKIE_BROWSER])
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
            
            if choice is None: return

            format_code = choice.split('|')[0].strip()
            print("\n")
            gum_style("Starting video download...")
            
            final_format = format_code
            if not has_audio_map.get(format_code, False):
                final_format += "+bestaudio"
            
            cmd = ["yt-dlp", "--force-overwrites", "--embed-metadata", "--embed-thumbnail"]
            if config.COOKIE_BROWSER:
                cmd.extend(["--cookies-from-browser", config.COOKIE_BROWSER])
            
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
    user_bin = config.get_user_bin_dir()
    
    print("\n")
    gum_style(f"Tools will be installed/updated in: {user_bin}", foreground="240")
    
    choice = gum_choose(["Yes, update", "Cancel"], header="Do you want to download the latest yt-dlp and svtplay-dl?")
    
    if choice is None or choice != "Yes, update":
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

    print("\n")
    gum_style("Done. Restart the program to use the new versions.", foreground="212")
    # Using input() here instead of gum_input() because we just want to pause, 
    # and gum_input logic is specifically for text entry.
    # But for consistency, let's use gum_input but ignore result.
    gum_input("Press Enter to continue...")

# --- Batch Download Functions ---

def download_youtube_silent(url, output_dir, mode="video"):
    """Download from YouTube without user interaction."""
    cmd = get_ytdlp_base_cmd()
    
    # Set output directory and template
    # Use -P for path to ensure it goes into the right folder
    cmd.extend(["-P", str(output_dir)])
    
    if mode == "video":
        cmd.extend([
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", "%(title)s.%(ext)s"
        ])
    else: # audio
        cmd.extend([
            "-f", "bestaudio/best", "-x", "--audio-format", "opus",
            "-o", "%(title)s.%(ext)s"
        ])
        
    cmd.append(url)
    
    return subprocess.run(cmd)

def download_svtplay_silent(url, output_dir, mode="video"):
    """Download from SVT Play without user interaction."""
    # svtplay-dl doesn't support -P easily, we might need to chdir or use absolute paths?
    # svtplay-dl usually downloads to current dir.
    # We can pass the URL and handle moving, or change cwd temporarily?
    # Changing CWD is risky in threads, but fine in single process.
    # Better: svtplay-dl documentation says output filename can be specified, but directory?
    # Let's use cwd argument in subprocess.run
    
    cmd = ["svtplay-dl", "-S", "-M"]
    if mode == "audio":
        cmd.append("--only-audio")
        
    cmd.append(url)
    
    return subprocess.run(cmd, cwd=output_dir)