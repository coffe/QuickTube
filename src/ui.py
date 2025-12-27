from rich import print as rprint
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED
from rich.console import Console
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

console = Console()

def gum_style(text, foreground=None, border=None, padding=None, border_foreground=None):
    """Wrapper for 'gum style' using Rich."""
    # Map 'gum' colors/styles to Rich
    style_str = ""
    if foreground:
        # gum uses ANSI colors (e.g. 212), Rich uses 'color(212)'
        style_str = f"color({foreground})"
    
    border_style_str = "white"
    if border_foreground:
        border_style_str = f"color({border_foreground})"

    if border:
        # gum default border is roughly equivalent to rounded
        # padding in gum "1 2" means 1 line vertical, 2 chars horizontal
        pad = (0, 1) # Default
        if padding:
            parts = padding.split()
            if len(parts) == 2:
                pad = (int(parts[0]), int(parts[1]))
            elif len(parts) == 1:
                pad = (int(parts[0]), int(parts[0]))
        
        # Create a Panel
        p = Panel(
            Text(text, style=style_str, justify="center" if border else "left"),
            border_style=border_style_str,
            box=ROUNDED,
            padding=pad,
            expand=False
        )
        rprint(p)
    else:
        # Just styled text
        rprint(Text(text, style=style_str))

def gum_input(placeholder, value=""):
    """Wrapper for 'gum input' using InquirerPy."""
    prompt = inquirer.text(
        message=placeholder, 
        default=value,
        qmark="",
        amark="",
        validate=lambda x: True
    )

    @prompt.register_kb("escape")
    def _(event):
        event.app.exit(result=None)

    return prompt.execute()

def gum_choose(choices, header=None):
    """Wrapper for 'gum choose' using InquirerPy."""
    if header:
        print("") # Newline for aesthetics
        gum_style(header, border="rounded", padding="1 2", border_foreground="240")
    
    # InquirerPy requires a message, but we can make it empty
    # We want to mimic the look of gum choose: list of options
    prompt = inquirer.select(
        message="", # No message
        choices=choices,
        qmark="",
        amark="",
        pointer=">", # Mimic gum pointer
        instruction="" # Hide "Press enter to continue" instructions
    )

    @prompt.register_kb("q")
    @prompt.register_kb("escape")
    def _(event):
        event.app.exit(result=None)

    return prompt.execute()

# Deprecated/Unused but kept for interface compatibility if needed
def gum_table(csv_data, header):
    pass