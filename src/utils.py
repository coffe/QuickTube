import os
import sys
import re
import subprocess
from datetime import datetime

def write_log(msg, console=True):
    """Write message to log file and optionally to console."""
    try:
        # Assuming log.txt is in the root of the application relative to this file
        # If this file is in src/utils.py, the root is one level up.
        # However, sys.argv[0] usually points to the entry script (main.py).
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        log_path = os.path.join(base_dir, "log.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Strip ANSI codes for the log file
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|[0-9A-FF?]*[ -/]*[0-9A-FF?~])')
        clean_msg = ansi_escape.sub('', str(msg))
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {clean_msg}\n")
    except Exception:
        pass # Ignore log errors

    if console:
        print(msg)

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
