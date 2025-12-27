import os
import sys
from pathlib import Path
from src.ui import gum_style, gum_choose
from src.core import download_youtube_silent, download_svtplay_silent, is_valid_url
from InquirerPy import inquirer

def handle_batch_download(file_path=None):
    """
    Handle batch downloading from a file.
    If file_path is None, prompt user to select a file.
    """
    
    # 1. Select File if not provided
    if not file_path:
        print("")
        gum_style("Enter the path to your link file (e.g. links.txt):", foreground="240")
        
        # Simple text input. Drag & drop usually works in terminals.
        file_path = inquirer.text(
            message="",
            qmark="",
            amark="",
            validate=lambda x: len(x) > 0 and os.path.isfile(x),
            invalid_message="File not found"
        ).execute()
        
        if not file_path: return

    # Verify file (double check if passed via arg)
    if not os.path.isfile(file_path):
        gum_style(f"File not found: {file_path}", foreground="196")
        return

    # 2. Select Mode
    mode_choice = gum_choose(
        ["Video (Best Quality)", "Audio (Opus/MP3)"], 
        header="Download mode for all links?"
    )
    
    if mode_choice is None: return
    
    mode = "video" if "Video" in mode_choice else "audio"

    # 3. Prepare Output Directory
    # Name folder same as filename without extension
    input_path = Path(file_path).resolve()
    output_dir = input_path.parent / input_path.stem
    
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        gum_style(f"Output directory: {output_dir}", foreground="212")
    except OSError as e:
        gum_style(f"Could not create directory: {e}", foreground="196")
        return

    # 4. Read Links
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Ignore lines starting with # or empty
            raw_lines = f.readlines()
    except Exception as e:
        gum_style(f"Error reading file: {e}", foreground="196")
        return
    
    links = [line.strip() for line in raw_lines if line.strip() and not line.strip().startswith("#")]
    
    if not links:
        gum_style("No valid links found in file.", foreground="196")
        return

    gum_style(f"Found {len(links)} links. Starting batch download...", foreground="212")
    print("")

    # 5. Process
    for i, url in enumerate(links, 1):
        # Validate URL vaguely
        if not is_valid_url(url):
            gum_style(f"[{i}/{len(links)}] Skipping invalid link: {url}", foreground="240")
            continue

        gum_style(f"[{i}/{len(links)}] Processing: {url}", foreground="212")
        
        if "svtplay.se" in url:
            res = download_svtplay_silent(url, output_dir, mode)
        else:
            res = download_youtube_silent(url, output_dir, mode)
            
        if res.returncode == 0:
            gum_style("✔ Done", foreground="212")
        else:
            gum_style("❌ Failed", foreground="196")
        print("")

    gum_style("Batch processing complete!", foreground="212")
    if not sys.argv[1:]: # Only pause if interactive
        input("Press Enter to continue...")
