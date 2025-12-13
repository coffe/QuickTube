#!/usr/bin/env python3
import subprocess
import shutil
import sys
import re
import json
import csv
import io

# --- Hjälpfunktioner för externa kommandon (GUM wrappers) ---

def run_command(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True):
    """Kör ett kommando och returnera resultatet."""
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
    """Wrapper för 'gum style'."""
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
    """Wrapper för 'gum input'."""
    cmd = ["gum", "input", "--placeholder", placeholder]
    if value:
        cmd.extend(["--value", value])
    
    # stderr=None låter gum rita UI:t till terminalen
    res = run_command(cmd, stderr=None)
    return res.stdout.strip() if res else ""

def gum_choose(choices, header=None):
    """Wrapper för 'gum choose'."""
    if header:
        print("") # Nyrad för snygghet
        gum_style(header, border="rounded", padding="1 2", border_foreground="240")
    
    cmd = ["gum", "choose"] + choices
    # stderr=None låter gum rita UI:t till terminalen
    res = run_command(cmd, stderr=None)
    return res.stdout.strip() if res else ""

def gum_table(csv_data, header):
    """Wrapper för 'gum table'."""
    # gum table förväntar sig CSV via stdin
    full_data = header + "\n" + csv_data
    process = subprocess.Popen(
        ["gum", "table", "-s", ",", "--height", "10"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None, # Låt stderr synas!
        text=True
    )
    stdout, _ = process.communicate(input=full_data)
    return stdout.strip()

# --- Kärnfunktioner ---

def check_dependencies():
    missing_deps = []
    dependencies = ["gum", "yt-dlp", "svtplay-dl", "mpv", "ffmpeg"]
    
    for dep in dependencies:
        if not shutil.which(dep):
            missing_deps.append(dep)
    
    # Kolla clipboard
    if not shutil.which("wl-paste") and not shutil.which("xclip"):
        missing_deps.append("wl-paste eller xclip")
        
    if missing_deps:
        gum_style("Fel: Följande beroenden saknas:", foreground="212")
        for dep in missing_deps:
            print(f"- {dep}")
        gum_style("Installera dem och försök igen.", foreground="212")
        sys.exit(1)

def get_clipboard():
    if shutil.which("wl-paste"):
        res = run_command(["wl-paste"])
        return res.stdout.strip().replace('\0', '')
    elif shutil.which("xclip"):
        res = run_command(["xclip", "-o", "-selection", "clipboard"])
        return res.stdout.strip().replace('\0', '')
    return ""

def is_valid_url(text):
    """Enkel kontroll om texten ser ut som en relevant URL."""
    patterns = [
        r"https?://(www\.)?youtube\.com/",
        r"https?://(www\.)?youtu\.be/",
        r"https?://(www\.)?svtplay\.se/"
    ]
    for pattern in patterns:
        if re.match(pattern, text):
            return True
    return False

# --- Huvudlogik ---

def handle_svtplay(url):
    header_text = "SVT Play-länk detekterad.\nVad vill du göra?"
    choices = [
        "Ladda ner (Bästa kvalitet + Undertexter)",
        "Ladda ner Hela Serien (-A)",
        "Ladda ner Hela Serien (yt-dlp)",
        "Ladda ner Specifika Avsnitt (yt-dlp)",
        "Ladda ner de X SISTA avsnitten (svtplay-dl)",
        "Stream (MPV)",
        "Ladda ner endast ljud"
    ]
    
    action = gum_choose(choices, header=header_text)
    
    if not action: return

    print("") # Spacer
    success = False

    if action == "Ladda ner (Bästa kvalitet + Undertexter)":
        gum_style("Startar nedladdning från SVT Play...")
        res = subprocess.run(["svtplay-dl", "-S", "-M", url])
        success = (res.returncode == 0)

    elif action == "Ladda ner Hela Serien (-A)":
        gum_style("Startar nedladdning av hela serien...")
        res = subprocess.run(["svtplay-dl", "-S", "-M", "-A", url])
        success = (res.returncode == 0)

    elif action == "Ladda ner Hela Serien (yt-dlp)":
        gum_style("Startar nedladdning av hela serien med yt-dlp...")
        cmd = [
            "yt-dlp", "--no-warnings", "--force-overwrites", "--embed-metadata", 
            "--embed-thumbnail", "--embed-subs", "--write-subs", "--sub-langs", "all",
            "-o", "%(series)s/S%(season_number)02dE%(episode_number)02d - %(title)s.%(ext)s",
            url
        ]
        res = subprocess.run(cmd)
        success = (res.returncode == 0)

    elif action == "Ladda ner Specifika Avsnitt (yt-dlp)":
        items = gum_input("Ange avsnitt (t.ex. 1, 2-5, 10)...")
        if items:
            gum_style(f"Laddar ner avsnitt {items} med yt-dlp...")
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

    elif action == "Ladda ner de X SISTA avsnitten (svtplay-dl)":
        count = gum_input("Antal avsnitt från slutet (t.ex. 5)...")
        if count.isdigit():
            gum_style(f"Laddar ner de sista {count} avsnitten...")
            res = subprocess.run(["svtplay-dl", "-S", "-M", "-A", "--all-last", count, url])
            success = (res.returncode == 0)
        else:
            gum_style("Felaktigt antal angivet.", foreground="196")
            return

    elif action == "Stream (MPV)":
        subprocess.run(["mpv", "--no-terminal", url])
        return "stream" # Signalera att vi streamade

    elif action == "Ladda ner endast ljud":
        gum_style("Laddar ner endast ljud...")
        res = subprocess.run(["svtplay-dl", "--only-audio", url])
        success = (res.returncode == 0)

    # Resultatmeddelande
    print("")
    if success:
        gum_style("✔ Nedladdning slutförd.", foreground="212")
    else:
        gum_style("❌ Nedladdning misslyckades.", foreground="196")
    
    return "download"

def handle_youtube(url):
    # Hämta info som JSON (säkrare än bash-parsing)
    res = run_command(["yt-dlp", "--flat-playlist", "--dump-json", "--no-warnings", url])
    
    if not res or res.returncode != 0:
        gum_style("Kunde inte hämta information för URL:en.", foreground="212")
        return

    try:
        # yt-dlp kan returnera flera JSON-objekt separerade med newline för spellistor
        first_line = res.stdout.strip().split('\n')[0]
        info = json.loads(first_line)
    except json.JSONDecodeError:
        gum_style("Kunde inte tolka videoinformation.", foreground="212")
        return

    title = info.get("title", "Okänd titel")
    is_playlist = info.get("_type") == "playlist" or "list=" in url
    
    formatted_title = f"{title[:57]}..." if len(title) > 60 else title

    if is_playlist:
        header = f"Vad vill du göra med spellistan:\n{formatted_title}?"
        choices = [
            "Stream Hela Spellistan (Video)", 
            "Stream Hela Spellistan (Ljud)",
            "Ladda ner Hela Spellistan (Video)", 
            "Ladda ner Hela Spellistan (Ljud)"
        ]
        action = gum_choose(choices, header=header)

        if action == "Stream Hela Spellistan (Video)":
            subprocess.run(["mpv", "--no-terminal", url])
            return "stream"
        elif action == "Stream Hela Spellistan (Ljud)":
            subprocess.run(["mpv", "--no-video", url])
            return "stream"
        
        # För nedladdning
        print("")
        cmd = ["yt-dlp", "--no-warnings", "--force-overwrites", "--embed-metadata", "--embed-thumbnail"]
        
        if action == "Ladda ner Hela Spellistan (Video)":
            gum_style("Startar nedladdning av hela spellistan (video)...")
            cmd.extend([
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "--merge-output-format", "mp4",
                "-o", "%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s",
                url
            ])
        elif action == "Ladda ner Hela Spellistan (Ljud)":
            gum_style("Startar nedladdning av hela spellistan (ljud)...")
            cmd.extend([
                "-f", "bestaudio", "-x", "--audio-format", "opus",
                "-o", "%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s",
                url
            ])
        
        subprocess.run(cmd)
        gum_style("✔ Nedladdning av spellista slutförd.", foreground="212")
        return "download"

    else:
        # Enskild video
        header = f"Vad vill du göra med:\n{formatted_title}?"
        choices = ["Stream Video (MPV)", "Stream Ljud (MPV)", "Ladda ner video", "Ladda ner ljud"]
        action = gum_choose(choices, header=header)

        if action == "Stream Video (MPV)":
            subprocess.run(["mpv", "--no-terminal", url])
            return "stream"
        elif action == "Stream Ljud (MPV)":
            subprocess.run(["mpv", "--no-video", url])
            return "stream"

        elif action == "Ladda ner ljud":
            print("")
            gum_style("Startar nedladdning av ljud...")
            # Hämta filnamn för städning (lite överkurs i Python kanske, yt-dlp sköter oftast detta, men följer scriptet)
            subprocess.run([
                "yt-dlp", "--no-warnings", "--force-overwrites", "--embed-metadata", 
                "--embed-thumbnail", "-f", "bestaudio", "-x", "--audio-format", "opus",
                "-o", "%(title)s.%(ext)s", url
            ])
            gum_style("✔ Nedladdning slutförd.", foreground="212")
            return "download"

        elif action == "Ladda ner video":
            # Hämta format via JSON istället för text-parsing (mycket robustare)
            res_fmt = run_command(["yt-dlp", "-J", url])
            if not res_fmt: return
            
            try:
                video_data = json.loads(res_fmt.stdout)
                formats = video_data.get("formats", [])
            except:
                return

            table_data = []
            # Skapa lista likt bash-scriptet: ID, Res, FPS, Ext, Codec, Storlek
            for f in formats:
                # Filtrera bort "video only" som inte är relevanta eller audio only
                if f.get("vcodec") == "none": continue 
                
                f_id = f.get("format_id", "N/A")
                ext = f.get("ext", "N/A")
                width = f.get("width")
                height = f.get("height")
                res = f"{width}x{height}" if width and height else "N/A"
                fps = f.get("fps", "N/A")
                vcodec = f.get("vcodec", "N/A")
                filesize = f.get("filesize") or f.get("filesize_approx")
                
                # Formatera storlek
                size_str = "N/A"
                if filesize:
                    size_str = f"{filesize / (1024*1024):.1f}MiB"

                table_data.append([f_id, res, fps, ext, vcodec, size_str])

            # Sortera (vi försöker efterlikna bash sort -t, -k2,2V -r men Pythonic)
            # Sorterar primärt på höjd (upplösning) fallande
            def sort_key(row):
                try:
                    res_part = row[1]
                    h = int(res_part.split('x')[1])
                    return h
                except:
                    return 0

            table_data.sort(key=sort_key, reverse=True)
            
            # Skapa CSV-sträng med csv-modulen
            csv_output = io.StringIO()
            writer = csv.writer(csv_output)
            writer.writerows(table_data)
            
            csv_string = csv_output.getvalue()
            header = "ID,Upplösning,FPS,Filtyp,Codec,Storlek"
            
            choice = gum_table(csv_string, header)
            
            if not choice: return

            format_code = choice.split(',')[0]
            print("")
            gum_style("Startar nedladdning av video...")
            subprocess.run([
                "yt-dlp", "--no-warnings", "--force-overwrites", "--embed-metadata", 
                "--embed-thumbnail", "-f", f"{format_code}+bestaudio", 
                "--merge-output-format", "mp4", 
                "-o", "%(title)s-%(height)sp.%(ext)s", url
            ])
            gum_style("✔ Nedladdning slutförd.", foreground="212")
            return "download"


def main():
    check_dependencies()
    last_action = ""

    while True:
        clipboard_content = get_clipboard()
        url_from_clipboard = ""

        # Förifyll bara om senaste åtgärden INTE var stream
        if last_action != "stream":
            cleaned = clipboard_content.strip()
            if is_valid_url(cleaned):
                url_from_clipboard = cleaned
        
        last_action = "" # Återställ

        url = gum_input("Klistra in/skriv en URL (YouTube/SVT Play)...", value=url_from_clipboard)

        if not url:
            gum_style("Ingen URL angiven. Avslutar.")
            break

        is_svt = "svtplay.se" in url
        
        if is_svt:
            last_action = handle_svtplay(url)
        else:
            last_action = handle_youtube(url)

        print("")
        next_step = gum_choose(["Ny länk", "Avsluta"])
        if next_step != "Ny länk":
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAvslutar...")
        sys.exit(0)
