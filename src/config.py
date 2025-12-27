import os
import sys
import shutil
import platform
from src.ui import gum_style

# Global setting
COOKIE_BROWSER = None

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

def get_user_config_dir():
    """Return the path to the user's config directory depending on OS."""
    system = platform.system()
    home = os.path.expanduser("~")
    
    if system == "Windows":
        return os.path.join(os.environ.get("APPDATA", home), "QuickTube")
    elif system == "Darwin": # macOS
        return os.path.join(home, "Library", "Application Support", "QuickTube")
    else: # Linux (XDG standard ish)
        return os.path.join(home, ".config", "QuickTube")

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
        # This file is in src/, so we go up one level to find the 'bin' folder in root
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dev_bin = os.path.join(root_dir, "bin")
        if os.path.exists(dev_bin):
            paths_to_add.append(dev_bin)
    
    # Add to PATH
    if paths_to_add:
        os.environ["PATH"] = os.pathsep.join(paths_to_add) + os.pathsep + os.environ["PATH"]

def check_dependencies():
    missing_deps = []
    # mpv and ffmpeg are expected on the system, gum/yt-dlp/svtplay-dl are bundled or in bin
    dependencies = ["yt-dlp", "svtplay-dl", "mpv", "ffmpeg"]
    
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