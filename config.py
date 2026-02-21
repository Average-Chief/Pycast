import os
MANUAL_COMMANDS = {
    "notepad":  "notepad",
    "explorer": "explorer",
    "youtube":  "start https://youtube.com",
    "github":   "start https://github.com",
    "gmail":    "start https://mail.google.com",
    "chatgpt":  "start https://chat.openai.com",
    "music":    "start https://music.amazon.in",
    "claude":   "start https://claude.ai",
    "deepseek": "start https://chat.deepseek.com/",
}

SCAN_DIRS = [
    r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
]

HOTKEY = "ctrl+alt+space"

# palette
BG          = "#1a1a1a"
BORDER_CLR  = "#323232"
DIVIDER_CLR = "#2a2a2a"

SEARCH_FG   = "#f0f0f0"
SEARCH_HINT = "#505050"
CARET_CLR   = "#ffffff"

ROW_BG      = "#1a1a1a"
ROW_HOV_BG  = "#242424"
ROW_SEL_BG  = "#1d3461"
ROW_SEL_BAR = "#4a9eff"

ROW_FG      = "#e0e0e0"
ROW_SEL_FG  = "#ffffff"
ROW_SUB_FG  = "#505050"
ROW_SEL_SUB = "#7aaeee"
NO_RES_FG   = "#404040"

ICON_BG     = "#282828"
ICON_FG     = "#606060"

# fonts
FONT_SEARCH = ("Segoe UI Light", 18)
FONT_NAME   = ("Segoe UI", 12)
FONT_SEL    = ("Segoe UI Semibold", 12)
FONT_SUB    = ("Segoe UI", 9)

# layout
WIDTH       = 640
SEARCH_H    = 64
ROW_H       = 48
ICON_SIZE   = 22
MAX_ROWS    = 7
PLACEHOLDER = "Search apps & commands…"