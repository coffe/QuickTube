import platform
import shutil
import subprocess
from src.utils import run_command

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
