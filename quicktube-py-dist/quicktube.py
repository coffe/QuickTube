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

def get_user_bin_dir():
    """Returnera sökvägen till användarens lokala bin-mapp beroende på OS."""
    system = platform.system()
    home = os.path.expanduser("~")
    
    if system == "Windows":
        return os.path.join(os.environ.get("APPDATA", home), "QuickTube", "bin")
    elif system == "Darwin": # macOS
        return os.path.join(home, "Library", "Application Support", "QuickTube", "bin")
    else: # Linux / annat
        return os.path.join(home, ".local", "bin", "quicktube_tools")

def setup_resources():
    """Konfigurera PATH för att inkludera binärer."""
    paths_to_add = []
    
    # 1. Användarens uppdaterade binärer (högst prio)
    user_bin = get_user_bin_dir()
    # Vi lägger till den även om den inte finns än, så subprocess hittar den om vi skapar den under körning
    paths_to_add.append(user_bin)
    
    # 2. Inbyggda binärer (PyInstaller)
    if hasattr(sys, '_MEIPASS'):
        # Om vi körs som en PyInstaller-exe
        bundle_bin = os.path.join(sys._MEIPASS, "bin")
        paths_to_add.append(bundle_bin)
    else:
        # Om vi körs som script (dev mode)
        dev_bin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
        if os.path.exists(dev_bin):
            paths_to_add.append(dev_bin)
    
    # Lägg till i PATH
    if paths_to_add:
        os.environ["PATH"] = os.pathsep.join(paths_to_add) + os.pathsep + os.environ["PATH"]

setup_resources()

# Global inställning
COOKIE_BROWSER = None

def get_ytdlp_base_cmd():
    """Returnera bas-kommando för yt-dlp inklusive cookies om valt."""
    cmd = ["yt-dlp", "--no-warnings", "--force-overwrites", "--embed-metadata", "--embed-thumbnail"]
    if COOKIE_BROWSER:
        cmd.extend(["--cookies-from-browser", COOKIE_BROWSER])
    return cmd

def select_cookie_browser():
    """Välj webbläsare för cookies."""
    global COOKIE_BROWSER
    
    browsers = ["Ingen (Standard)", "chrome", "firefox", "brave", "edge", "safari", "opera", "vivaldi", "chromium"]
    choice = gum_choose(browsers, header="Välj webbläsare att låna cookies från (löser ofta 'Bot' fel):")
    
    if choice and choice != "Ingen (Standard)":
        COOKIE_BROWSER = choice
        gum_style(f"Webbläsare vald: {COOKIE_BROWSER}", foreground="212")
    else:
        COOKIE_BROWSER = None
        gum_style("Cookies inaktiverade.", foreground="212")

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
        cmd = get_ytdlp_base_cmd()
        cmd.extend([
            "--embed-subs", "--write-subs", "--sub-langs", "all",
            "-o", "%(series)s/S%(season_number)02dE%(episode_number)02d - %(title)s.%(ext)s",
            url
        ])
        res = subprocess.run(cmd)
        success = (res.returncode == 0)

    elif action == "Ladda ner Specifika Avsnitt (yt-dlp)":
        items = gum_input("Ange avsnitt (t.ex. 1, 2-5, 10)...")
        if items:
            gum_style(f"Laddar ner avsnitt {items} med yt-dlp...")
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
    info_cmd = ["yt-dlp", "--flat-playlist", "--dump-json", "--no-warnings"]
    if COOKIE_BROWSER: info_cmd.extend(["--cookies-from-browser", COOKIE_BROWSER])
    info_cmd.append(url)
    
    res = run_command(info_cmd)
    
    if not res or res.returncode != 0:
        gum_style("Kunde inte hämta information för URL:en.", foreground="212")
        if not COOKIE_BROWSER:
            gum_style("Tips: Prova att välja en webbläsare för cookies i huvudmenyn.", foreground="240")
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
        cmd = get_ytdlp_base_cmd()
        
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
            cmd = get_ytdlp_base_cmd()
            cmd.extend([
                "-f", "bestaudio", "-x", "--audio-format", "opus",
                "-o", "%(title)s.%(ext)s", url
            ])
            subprocess.run(cmd)
            gum_style("✔ Nedladdning slutförd.", foreground="212")
            return "download"

        elif action == "Ladda ner video":
            # Hämta format via JSON istället för text-parsing (mycket robustare)
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
            
            cmd = get_ytdlp_base_cmd()
            cmd.extend([
                "-f", f"{format_code}+bestaudio", 
                "--merge-output-format", "mp4", 
                "-o", "%(title)s-%(height)sp.%(ext)s", url
            ])
            
            subprocess.run(cmd)
            gum_style("✔ Nedladdning slutförd.", foreground="212")
            return "download"


def update_tools():
    """Ladda ner senaste versionerna av verktygen."""
    user_bin = get_user_bin_dir()
    
    print("")
    gum_style(f"Verktyg installeras/uppdateras i: {user_bin}", foreground="240")
    
    # Bekräfta
    if gum_choose(["Ja, uppdatera", "Avbryt"], header="Vill du ladda ner senaste yt-dlp och svtplay-dl?") != "Ja, uppdatera":
        return

    # Skapa mapp
    try:
        os.makedirs(user_bin, exist_ok=True)
    except OSError as e:
        gum_style(f"Kunde inte skapa mapp: {e}", foreground="196")
        return
    
    system = platform.system()
    
    # --- YT-DLP ---
    # GitHub releases
    ytdlp_filename_remote = "yt-dlp"
    if system == "Windows": ytdlp_filename_remote = "yt-dlp.exe"
    elif system == "Darwin": ytdlp_filename_remote = "yt-dlp_macos"
    
    ytdlp_url = f"https://github.com/yt-dlp/yt-dlp/releases/latest/download/{ytdlp_filename_remote}"
    ytdlp_local = "yt-dlp.exe" if system == "Windows" else "yt-dlp"
    
    gum_style("Laddar ner senaste yt-dlp...", foreground="212")
    try:
        urllib.request.urlretrieve(ytdlp_url, os.path.join(user_bin, ytdlp_local))
        if system != "Windows":
            os.chmod(os.path.join(user_bin, ytdlp_local), 0o755)
        gum_style("✔ yt-dlp uppdaterad.", foreground="212")
    except Exception as e:
        gum_style(f"❌ Misslyckades uppdatera yt-dlp: {e}", foreground="196")

    # --- SVTPLAY-DL ---
    if system != "Darwin":
        svt_remote = "svtplay-dl.exe" if system == "Windows" else "svtplay-dl"
        svt_url = f"https://svtplay-dl.se/download/latest/{svt_remote}"
        
        gum_style("Laddar ner senaste svtplay-dl...", foreground="212")
        try:
            urllib.request.urlretrieve(svt_url, os.path.join(user_bin, svt_remote))
            if system != "Windows":
                os.chmod(os.path.join(user_bin, svt_remote), 0o755)
            gum_style("✔ svtplay-dl uppdaterad.", foreground="212")
        except Exception as e:
            gum_style(f"❌ Misslyckades uppdatera svtplay-dl: {e}", foreground="196")
    else:
         gum_style("ℹ️  svtplay-dl uppdatering på Mac kräver manuell hantering (zip).", foreground="240")

    print("")
    gum_style("Klart. Starta om programmet för att använda nya versioner.", foreground="212")
    input("Tryck Enter för att fortsätta...")


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

        url = gum_input("Klistra in/skriv en URL (lämna tomt för meny)...", value=url_from_clipboard)

        if not url:
            # Om tomt, visa huvudmeny
            choice = gum_choose(["Klistra in länk", "Uppdatera verktyg", "Välj webbläsare för cookies", "Avsluta"], header="Huvudmeny")
            
            if choice == "Uppdatera verktyg":
                update_tools()
                continue
            elif choice == "Välj webbläsare för cookies":
                select_cookie_browser()
                continue
            elif choice == "Avsluta":
                break
            elif choice == "Klistra in länk":
                continue # Loopa om för att be om URL igen

        is_svt = "svtplay.se" in url
        
        if is_svt:
            last_action = handle_svtplay(url)
        else:
            last_action = handle_youtube(url)

        print("")
        next_step = gum_choose(["Ny länk", "Uppdatera verktyg", "Välj webbläsare för cookies", "Avsluta"])
        
        if next_step == "Uppdatera verktyg":
            update_tools()
        elif next_step == "Välj webbläsare för cookies":
            select_cookie_browser()
        elif next_step != "Ny länk":
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAvslutar...")
        sys.exit(0)
