#!/usr/bin/env python3
import subprocess
import shutil
import sys
import re
import json
import csv
import io

# --- Helper functions for external commands (GUM wrappers) ---

def run_command(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, 
            stdout=stdout,
            stderr=stderr,
            text=text, 
            check=False
        )
        return result
    except FileNotFoundError:
        return None

def gum_style(text, foreground=None, border=None, padding=None, border_foreground=None):
    """Wrapper for "gum style"."""
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
    """Wrapper for "gum input"."""
    cmd = ["gum", "input", "--placeholder", placeholder]
    if value:
        cmd.extend(["--value", value])
    
    # stderr=None lets gum draw the UI to the terminal
    res = run_command(cmd, stderr=None)
    return res.stdout.strip() if res else ""

def gum_choose(choices, header=None):
    """Wrapper for "gum choose"."""
    if header:
        print("") # Newline for aesthetics
        gum_style(header, border="rounded", padding="1 2", border_foreground="240")
    
    cmd = ["gum", "choose"] + choices
    # stderr=None lets gum draw the UI to the terminal
    res = run_command(cmd, stderr=None)
    return res.stdout.strip() if res else ""


def gum_table(csv_data, header):
    """Wrapper for "gum table"."""
    # gum table expects CSV via stdin
    full_data = header + "\n" + csv_data
    process = subprocess.Popen(
        ["gum", "table", "-s", ",", "--height", "10"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None, # Let stderr be visible!
        text=True
    )
    stdout, _ = process.communicate(input=full_data)
    return stdout.strip()

# --- Core functions ---

def check_dependencies():
    missing_deps = []
    dependencies = ["gum", "yt-dlp", "svtplay-dl", "mpv", "ffmpeg"]
    
    for dep in dependencies:
        if not shutil.which(dep):
            missing_deps.append(dep)
    
    # Check clipboard
    if not shutil.which("wl-paste") and not shutil.which("xclip"):
        missing_deps.append("wl-paste or xclip")
        
    if missing_deps:
        gum_style("Error: The following dependencies are missing:", foreground="212")
        for dep in missing_deps:
            print(f"- {dep}")
        gum_style("Please install them and try again.", foreground="212")
        sys.exit(1)

def get_clipboard():
    if shutil.which("wl-paste"):
        res = run_command(["wl-paste"])
        return res.stdout.strip().replace("\0", "")
    elif shutil.which("xclip"):
        res = run_command(["xclip", "-o", "-selection", "clipboard"])
        return res.stdout.strip().replace("\0", "")
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
        cmd = [
            "yt-dlp", "--no-warnings", "--force-overwrites", "--embed-metadata", 
            "--embed-thumbnail", "--embed-subs", "--write-subs", "--sub-langs", "all",
            "-o", "%(series)s/S%(season_number)02dE%(episode_number)02d - %(title)s.%(ext)s",
            url
        ]
        res = subprocess.run(cmd)
        success = (res.returncode == 0)

    elif action == "Download Specific Episodes (yt-dlp)":
        items = gum_input("Enter episodes (e.g., 1, 2-5, 10)...")
        if items:
            gum_style(f"Downloading episodes {items} with yt-dlp...")
            cmd = [
                "yt-dlp", "--no-warnings", "--force-overwrites", "--embed-metadata",
                "--embed-thumbnail", "--embed-subs", "--write-subs", "--sub-langs", "all",
                "--playlist-items", items,
                "-o", "%(series)s/S%(season_number)02dE%(episode_number)02d - %(title)s.%(ext)s",
                url
            ]
            res = subprocess.run(cmd)
            success = (res.returncode == 0)
        else:
            return

    elif action == "Download the LAST X episodes (svtplay-dl)":
        count = gum_input("Number of episodes from the end (e.g., 5)...")
        if count.isdigit():
            gum_style(f"Downloading the last {count} episodes...")
            res = subprocess.run(["svtplay-dl", "-S", "-M", "-A", "--all-last", count, url])
            success = (res.returncode == 0)
        else:
            gum_style("Invalid number specified.", foreground="196")
            return

    elif action == "Stream (MPV)":
        subprocess.run(["mpv", "--no-terminal", url])
        return "stream" # Signal that we streamed

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
    # Get info as JSON (safer than bash parsing)
    res = run_command(["yt-dlp", "--flat-playlist", "--dump-json", "--no-warnings", url])
    
    if not res or res.returncode != 0:
        gum_style("Could not retrieve information for the URL.", foreground="212")
        return

    try:
        # yt-dlp can return multiple JSON objects separated by newline for playlists
        first_line = res.stdout.strip().split("\n")[0]
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
        cmd = ["yt-dlp", "--no-warnings", "--force-overwrites", "--embed-metadata", "--embed-thumbnail"]
        
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
                "-f", "bestaudio", "-x", "--audio-format", "opus",
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
            # Get filename for cleanup (a bit overkill in Python perhaps, yt-dlp usually handles this, but following the script)
            subprocess.run([
                "yt-dlp", "--no-warnings", "--force-overwrites", "--embed-metadata", 
                "--embed-thumbnail", "-f", "bestaudio", "-x", "--audio-format", "opus",
                "-o", "%(title)s.%(ext)s", url
            ])
            gum_style("✔ Download complete.", foreground="212")
            return "download"


        elif action == "Download video":
            # Get format via JSON instead of text parsing (much more robust)
            res_fmt = run_command(["yt-dlp", "-J", url])
            if not res_fmt: return
            
            try:
                video_data = json.loads(res_fmt.stdout)
                formats = video_data.get("formats", [])
            except:
                return

            table_data = []
            # Create list like the bash script: ID, Res, FPS, Ext, Codec, Size
            for f in formats:
                # Filter out "video only" that are not relevant or audio only
                if f.get("vcodec") == "none": continue 
                
                f_id = f.get("format_id", "N/A")
                ext = f.get("ext", "N/A")
                width = f.get("width")
                height = f.get("height")
                res = f"{width}x{height}" if width and height else "N/A"
                fps = f.get("fps", "N/A")
                vcodec = f.get("vcodec", "N/A")
                filesize = f.get("filesize") or f.get("filesize_approx")
                
                # Format size
                size_str = "N/A"
                if filesize:
                    size_str = f"{filesize / (1024*1024):.1f}MiB"

                table_data.append([f_id, res, fps, ext, vcodec, size_str])

            # Sort (trying to mimic bash sort -t, -k2,2V -r but Pythonic)
            # Sorts primarily on height (resolution) descending
            def sort_key(row):
                try:
                    res_part = row[1]
                    h = int(res_part.split('x')[1])
                    return h
                except:
                    return 0

            table_data.sort(key=sort_key, reverse=True)
            
            # Create CSV string with csv module
            csv_output = io.StringIO()
            writer = csv.writer(csv_output)
            writer.writerows(table_data)
            
            csv_string = csv_output.getvalue()
            header = "ID,Resolution,FPS,Filetype,Codec,Size"
            
            choice = gum_table(csv_string, header)
            
            if not choice: return

            format_code = choice.split(',')[0]
            print("")
            gum_style("Starting video download...")
            subprocess.run([
                "yt-dlp", "--no-warnings", "--force-overwrites", "--embed-metadata", 
                "--embed-thumbnail", "-f", f"{format_code}+bestaudio", 
                "--merge-output-format", "mp4", 
                "-o", "%(title)s-%(height)sp.%(ext)s", url
            ])
            gum_style("✔ Download complete.", foreground="212")
            return "download"


def main():
    check_dependencies()
    last_action = ""

    while True:
        clipboard_content = get_clipboard()
        url_from_clipboard = ""

        # Pre-fill only if the last action was NOT stream
        if last_action != "stream":
            cleaned = clipboard_content.strip()
            if is_valid_url(cleaned):
                url_from_clipboard = cleaned
        
        last_action = "" # Reset

        url = gum_input("Paste/enter a URL (YouTube/SVT Play)...", value=url_from_clipboard)

        if not url:
            gum_style("No URL specified. Exiting.")
            break

        is_svt = "svtplay.se" in url
        
        if is_svt:
            last_action = handle_svtplay(url)
        else:
            last_action = handle_youtube(url)

        print("")
        next_step = gum_choose(["New link", "Exit"])
        if next_step != "New link":
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

