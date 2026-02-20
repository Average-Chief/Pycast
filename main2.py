import subprocess
import tkinter as tk
from threading import Event, Thread
import keyboard
import os
import glob
import ctypes
import ctypes.wintypes
import sys

# ── optional icon deps ────────────────────────────────────────────────────
# pip install pywin32 pillow
try:
    import win32ui, win32gui, win32con, win32api
    import win32com.client
    from PIL import Image, ImageTk
    ICONS_AVAILABLE = True
except ImportError:
    ICONS_AVAILABLE = False
    print("[launcher] pip install pywin32 pillow  → to get app icons")

# ─────────────────────────────────────────────
#  MANUAL COMMANDS
# ─────────────────────────────────────────────
MANUAL_COMMANDS = {
    "notepad":  "notepad",
    "explorer": "explorer",
    "youtube":  "start https://youtube.com",
    "github":   "start https://github.com",
    "gmail":    "start https://mail.google.com",
}

SCAN_DIRS = [
    r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
]

HOTKEY = "ctrl+alt+space"

# ─────────────────────────────────────────────
#  FLUENT / ACRYLIC BLUR  via ctypes
#
#  How it works:
#  1. Mark one colour as "transparent" so DWM can see through it.
#  2. Call SetWindowCompositionAttribute with ACCENT_ENABLE_ACRYLICBLURBEHIND
#     (Win10 1703+) which tells DWM to render the Acrylic material behind our
#     window.  Older builds fall back to ACCENT_ENABLE_BLURBEHIND (Win10 1507).
#  3. All tkinter widgets use a semi-opaque dark colour so text/icons are
#     readable on top of the blurred desktop.
# ─────────────────────────────────────────────

TRANSPARENT_KEY = "#010101"   # the colour we punch through to DWM

class _ACCENTPOLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState",   ctypes.c_uint),
        ("AccentFlags",   ctypes.c_uint),
        ("GradientColor", ctypes.c_uint),   # AABBGGRR
        ("AnimationId",   ctypes.c_uint),
    ]

class _WINCOMPATTRDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute",  ctypes.c_int),
        ("pData",      ctypes.c_void_p),
        ("DataSize",   ctypes.wintypes.ULONG),
    ]

_ACCENT_DISABLED              = 0
_ACCENT_ENABLE_BLURBEHIND     = 3   # Win10 RTM
_ACCENT_ENABLE_ACRYLICBLURBEHIND = 4   # Win10 1703+
_WCA_ACCENT_POLICY            = 19


def apply_blur(hwnd: int, dark: bool = True) -> bool:
    """
    Apply Acrylic blur to `hwnd`.
    `dark=True`  → dark tinted acrylic (our theme).
    Returns True on success.
    """
    try:
        user32 = ctypes.windll.user32
        # GradientColor = AABBGGRR  (AA=alpha tint, rest = tint colour)
        # AA=CC → ~80 % opaque tint  gives a nice dark-but-see-through panel
        tint = 0xCC1A1A1A if dark else 0xCCF5F5F5

        policy = _ACCENTPOLICY()
        policy.AccentState   = _ACCENT_ENABLE_ACRYLICBLURBEHIND
        policy.AccentFlags   = 2          # draw border
        policy.GradientColor = tint
        policy.AnimationId   = 0

        data = _WINCOMPATTRDATA()
        data.Attribute = _WCA_ACCENT_POLICY
        data.pData     = ctypes.cast(ctypes.pointer(policy), ctypes.c_void_p)
        data.DataSize  = ctypes.sizeof(policy)

        result = user32.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))
        if result:
            return True

        # Fallback: plain blur (no tint, Win10 RTM – 1607)
        policy.AccentState   = _ACCENT_ENABLE_BLURBEHIND
        policy.GradientColor = 0
        result = user32.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))
        return bool(result)
    except Exception as exc:
        print(f"[blur] failed: {exc}")
        return False


def enable_blur_on_window(root_widget):
    """
    Call after the window is visible.
    Also punches the transparent colour so DWM shows through.
    """
    root_widget.update_idletasks()
    hwnd = ctypes.windll.user32.FindWindowW(None, root_widget.title())
    if not hwnd:
        # fallback: use winfo_id of the root
        hwnd = root_widget.winfo_id()
    ok = apply_blur(hwnd)
    if ok:
        # Tell tkinter to treat TRANSPARENT_KEY as see-through
        root_widget.wm_attributes("-transparentcolor", TRANSPARENT_KEY)
    print(f"[blur] {'acrylic enabled' if ok else 'not supported on this Windows build'}")
    return ok

# ─────────────────────────────────────────────
#  DESIGN TOKENS  — translucent dark panel
#
#  Because DWM blurs the desktop behind the window, all solid-background
#  widgets need to use a colour that blends nicely with whatever is behind.
#  We use semi-dark values; the acrylic tint (0xCC1A1A1A above) does the
#  rest of the work.
# ─────────────────────────────────────────────

# TRANSPARENT_KEY is punched out to DWM — use it as the base bg for root
# All child widgets use BG which is a very dark grey.
# We keep a little opacity so text is always readable.
BG          = "#1a1a1a"       # main panel bg  (matches the acrylic tint colour)
BORDER_CLR  = "#323232"       # 1 px border
DIVIDER_CLR = "#2a2a2a"

SEARCH_FG   = "#f0f0f0"
SEARCH_HINT = "#505050"
CARET_CLR   = "#ffffff"

ROW_BG      = "#1a1a1a"
ROW_HOV_BG  = "#242424"
ROW_SEL_BG  = "#1d3461"       # deep navy selection
ROW_SEL_BAR = "#4a9eff"       # bright Fluent blue accent bar
ROW_FG      = "#e0e0e0"
ROW_SEL_FG  = "#ffffff"
ROW_SUB_FG  = "#505050"
ROW_SEL_SUB = "#7aaeee"
NO_RES_FG   = "#404040"

ICON_BG     = "#282828"
ICON_FG     = "#606060"

FONT_SEARCH = ("Segoe UI Light", 18)
FONT_NAME   = ("Segoe UI",       12)
FONT_SEL    = ("Segoe UI Semibold", 12)
FONT_SUB    = ("Segoe UI",        9)

WIDTH       = 640
SEARCH_H    = 64
ROW_H       = 48
ICON_SIZE   = 22
MAX_ROWS    = 7
PLACEHOLDER = "Search apps & commands…"

# ─────────────────────────────────────────────
#  APP SCANNING
# ─────────────────────────────────────────────
def scan_lnk_files():
    found = {}
    skip  = ("uninstall", "help", "readme", "release notes", "documentation")
    for d in SCAN_DIRS:
        if not os.path.isdir(d):
            continue
        for lnk in glob.glob(os.path.join(d, "**", "*.lnk"), recursive=True):
            name = os.path.splitext(os.path.basename(lnk))[0].lower()
            if any(w in name for w in skip):
                continue
            if name not in found:
                found[name] = lnk
    return found

def build_commands():
    table = scan_lnk_files()
    for k, v in MANUAL_COMMANDS.items():
        table[k] = os.path.expandvars(v)
    return table

COMMANDS = build_commands()
print(f"[launcher] {len(COMMANDS)} commands loaded")

# ─────────────────────────────────────────────
#  ICON EXTRACTION
#  Three methods tried in order:
#   1. SHGetFileInfo  — fastest, works on .lnk directly
#   2. ExtractIconEx  — works on .exe targets directly
#   3. PrivateExtractIcons — last resort, handles more edge cases
# ─────────────────────────────────────────────
_icon_cache: dict = {}
_shell = None

def _get_shell():
    global _shell
    if _shell is None and ICONS_AVAILABLE:
        try:
            _shell = win32com.client.Dispatch("WScript.Shell")
        except Exception:
            pass
    return _shell

def _resolve_lnk(path: str) -> str:
    """Follow a .lnk and return the target exe path."""
    try:
        sh = _get_shell()
        if sh:
            sc  = sh.CreateShortCut(path)
            tgt = sc.TargetPath
            if tgt and os.path.exists(tgt):
                return tgt
    except Exception:
        pass
    return path   # give up, use lnk path itself for icon lookup

def _hicon_to_pil(hicon: int, size: int) -> "Image.Image":
    """Render a Windows HICON into a PIL RGBA image."""
    # create an in-memory DC + bitmap the right size
    screen_dc = win32gui.GetDC(0)
    hdc       = win32ui.CreateDCFromHandle(screen_dc)
    mem_dc    = hdc.CreateCompatibleDC()
    bmp       = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(hdc, size, size)
    old_bmp   = mem_dc.SelectObject(bmp)

    # clear to black-transparent
    mem_dc.FillSolidRect((0, 0, size, size), 0x00000000)

    # draw the icon
    win32gui.DrawIconEx(
        mem_dc.GetSafeHdc(), 0, 0, hicon,
        size, size, 0, None, win32con.DI_NORMAL
    )

    # pull raw BGRA bytes
    info = bmp.GetInfo()
    bits = bmp.GetBitmapBits(True)

    # clean up Windows resources
    mem_dc.SelectObject(old_bmp)
    mem_dc.DeleteDC()
    hdc.DeleteDC()
    win32gui.ReleaseDC(0, screen_dc)
    win32gui.DestroyIcon(hicon)

    return Image.frombuffer(
        "RGBA",
        (info["bmWidth"], info["bmHeight"]),
        bits, "raw", "BGRA", 0, 1
    )

# ── Method 1: SHGetFileInfo ───────────────────────────────────────────────
def _extract_via_shgetfileinfo(path: str, size: int) -> "Image.Image | None":
    """
    Use Shell32 SHGetFileInfo — most reliable for .lnk files.
    pywin32 SHGetFileInfo signature: SHGetFileInfo(pszPath, dwFileAttributes, uFlags)
    Returns: (hIcon, iIcon, dwAttributes, szDisplayName, szTypeName)
    """
    try:
        # SHGFI_ICON | SHGFI_LARGEICON for a 32x32 icon
        SHGFI_ICON      = 0x000000100
        SHGFI_LARGEICON = 0x000000000
        SHGFI_SMALLICON = 0x000000001

        flags = SHGFI_ICON | (SHGFI_LARGEICON if size >= 32 else SHGFI_SMALLICON)
        ret   = win32api.SHGetFileInfo(path, 0, flags)
        # ret is a tuple: (hIcon, iIcon, dwAttributes, szDisplayName, szTypeName)
        hicon = ret[0]
        if not hicon:
            return None
        return _hicon_to_pil(hicon, size)
    except Exception as e:
        return None

# ── Method 2: ExtractIconEx ───────────────────────────────────────────────
def _extract_via_extracticonex(path: str, size: int) -> "Image.Image | None":
    """
    Use Shell32 ExtractIconEx directly on the .exe (or .lnk target).
    """
    try:
        target = _resolve_lnk(path) if path.lower().endswith(".lnk") else path
        if not os.path.exists(target):
            return None

        large_icons, small_icons = win32gui.ExtractIconEx(target, 0, 1)
        hicons = large_icons if size >= 32 else small_icons
        # the other list still has HICONs that need destroying
        for h in (small_icons if size >= 32 else large_icons):
            if h: win32gui.DestroyIcon(h)

        if not hicons or not hicons[0]:
            return None
        return _hicon_to_pil(hicons[0], size)
    except Exception:
        return None

# ── Method 3: PrivateExtractIcons (pure ctypes, no pywin32 needed) ────────
def _extract_via_private(path: str, size: int) -> "Image.Image | None":
    """
    PrivateExtractIcons is an undocumented but reliable Win32 API
    that works even when the other two fail.
    """
    try:
        target = _resolve_lnk(path) if path.lower().endswith(".lnk") else path
        if not os.path.exists(target):
            return None

        hicon   = ctypes.wintypes.HICON()
        hicon_i = ctypes.wintypes.UINT()
        n = ctypes.windll.user32.PrivateExtractIconsW(
            target, 0, size, size,
            ctypes.byref(hicon), ctypes.byref(hicon_i),
            1, 0
        )
        if n == 0 or not hicon.value:
            return None

        img = _hicon_to_pil(hicon.value, size)
        return img
    except Exception:
        return None

# ── Master extractor ──────────────────────────────────────────────────────
def _extract_icon(path: str, size: int = 32) -> "Image.Image | None":
    if not path:
        return None

    # try all three methods
    for method in (_extract_via_shgetfileinfo,
                   _extract_via_extracticonex,
                   _extract_via_private):
        try:
            img = method(path, size)
            if img is not None:
                return img
        except Exception:
            continue
    return None

def get_icon(name: str) -> "ImageTk.PhotoImage | None":
    if not ICONS_AVAILABLE:
        return None
    if name in _icon_cache:
        return _icon_cache[name]

    cmd   = COMMANDS.get(name, "")
    photo = None

    # extract at 2× then downsample for crisp result
    img = _extract_icon(cmd, size=ICON_SIZE * 2)
    if img:
        img   = img.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)

    _icon_cache[name] = photo
    return photo

def preload_icons_async(names):
    def _w():
        for n in names:
            get_icon(n)
    Thread(target=_w, daemon=True).start()

# ─────────────────────────────────────────────
#  FUZZY MATCHING
# ─────────────────────────────────────────────
def fuzzy_score(q, name):
    n = name.lower(); q = q.lower()
    if q == n:           return 4
    if n.startswith(q):  return 3
    if q in n:           return 2
    it = iter(n)
    if all(c in it for c in q): return 1
    return 0

def get_matches(query):
    q = query.strip()
    if not q:
        return sorted(COMMANDS.keys())
    scored = [(fuzzy_score(q, k), k) for k in COMMANDS if fuzzy_score(q, k) > 0]
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [k for _, k in scored]

# ─────────────────────────────────────────────
#  LAUNCH
# ─────────────────────────────────────────────
def launch(name):
    if name not in COMMANDS:
        return
    cmd = COMMANDS[name]
    if cmd.endswith(".lnk"):       os.startfile(cmd)
    elif cmd.startswith("start "): subprocess.Popen(cmd, shell=True)
    elif cmd.endswith(".exe"):     subprocess.Popen([cmd])
    else:                          subprocess.Popen(cmd, shell=True)

# ─────────────────────────────────────────────
#  STATE
# ─────────────────────────────────────────────
show_event = Event()
selected   = 0
matches    = []
blur_ok    = False   # set after window shown

# ─────────────────────────────────────────────
#  WINDOW SIZING
# ─────────────────────────────────────────────
def set_geometry(rows):
    h  = SEARCH_H
    if rows > 0:
        h += 1 + rows * ROW_H + 8
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{WIDTH}x{h}+{(sw - WIDTH)//2}+{sh//3}")

# ─────────────────────────────────────────────
#  ROW DRAWING
# ─────────────────────────────────────────────
def draw_row(parent, idx, name, is_sel):
    row_bg  = ROW_SEL_BG if is_sel else ROW_BG
    text_fg = ROW_SEL_FG if is_sel else ROW_FG
    sub_fg  = ROW_SEL_SUB if is_sel else ROW_SUB_FG
    fn      = FONT_SEL    if is_sel else FONT_NAME

    outer = tk.Frame(parent, bg=row_bg, height=ROW_H)
    outer.pack(fill="x")
    outer.pack_propagate(False)

    tk.Frame(outer, bg=ROW_SEL_BAR if is_sel else row_bg, width=3).pack(side="left", fill="y")

    inner = tk.Frame(outer, bg=row_bg)
    inner.pack(side="left", fill="both", expand=True)

    # icon
    photo = get_icon(name)
    if photo:
        lbl = tk.Label(inner, image=photo, bg=row_bg, bd=0)
        lbl.image = photo
        lbl.place(x=12, rely=0.5, anchor="w")
    else:
        ic = tk.Frame(inner, bg=ICON_BG, width=ICON_SIZE, height=ICON_SIZE)
        ic.place(x=12, rely=0.5, anchor="w")
        tk.Label(ic, text=name[0].upper(), font=("Segoe UI Semibold", 8),
                 bg=ICON_BG, fg=ICON_FG).place(relx=0.5, rely=0.5, anchor="center")

    TEXT_X = 12 + ICON_SIZE + 10
    tk.Label(inner, text=name, font=fn, bg=row_bg, fg=text_fg, anchor="w").place(
        x=TEXT_X, rely=0.5, anchor="w")

    cmd  = COMMANDS[name]
    hint = os.path.basename(cmd) if os.path.isabs(cmd) else cmd
    if len(hint) > 38: hint = "…" + hint[-36:]
    tk.Label(inner, text=hint, font=FONT_SUB, bg=row_bg, fg=sub_fg, anchor="e").place(
        relx=1.0, x=-14, rely=0.5, anchor="e")

    if not is_sel:
        tk.Frame(outer, bg=DIVIDER_CLR, height=1).place(
            relx=0, rely=1.0, anchor="sw", relwidth=1.0)

    all_w = [outer, inner] + list(inner.winfo_children())

    def enter(e, o=outer, f=inner, i=idx):
        if i != selected:
            for w in (o, f): w.config(bg=ROW_HOV_BG)
            for c in f.winfo_children(): c.config(bg=ROW_HOV_BG)

    def leave(e, o=outer, f=inner, i=idx):
        if i != selected:
            for w in (o, f): w.config(bg=ROW_BG)
            for c in f.winfo_children(): c.config(bg=ROW_BG)

    for w in all_w:
        w.bind("<Button-1>", lambda e, n=name: confirm(n))
        w.bind("<Enter>",    enter)
        w.bind("<Leave>",    leave)

# ─────────────────────────────────────────────
#  REDRAW
# ─────────────────────────────────────────────
def redraw():
    for w in list_frame.winfo_children():
        w.destroy()

    n_visible = min(len(matches), MAX_ROWS)

    if n_visible == 0:
        q = entry_var.get().strip()
        if q and q != PLACEHOLDER:
            tk.Label(list_frame, text="No results", font=FONT_SUB,
                     bg=BG, fg=NO_RES_FG, anchor="w").pack(fill="x", padx=20, pady=12)
            set_geometry(rows=1)
        else:
            set_geometry(rows=0)
        return

    for i, name in enumerate(matches[:MAX_ROWS]):
        draw_row(list_frame, i, name, i == selected)

    set_geometry(rows=n_visible)

    if ICONS_AVAILABLE:
        preload_icons_async(matches[:MAX_ROWS])

# ─────────────────────────────────────────────
#  ACTIONS
# ─────────────────────────────────────────────
def update_list(*_):
    global matches, selected
    text = entry_var.get()
    if text == PLACEHOLDER or text == "":
        matches = []; selected = 0; redraw(); return
    matches  = get_matches(text)
    selected = 0
    redraw()

def move_selection(delta):
    global selected
    if not matches: return
    selected = (selected + delta) % min(len(matches), MAX_ROWS)
    redraw()

def confirm(name=None):
    n = name or (matches[selected] if matches else None)
    if n: launch(n)
    hide()

def hide(event=None):
    entry_var.set(PLACEHOLDER)
    entry.config(fg=SEARCH_HINT)
    root.withdraw()

def on_entry_click(event=None):
    if entry_var.get() == PLACEHOLDER:
        entry.config(fg=SEARCH_FG)
        entry_var.set("")

def on_entry_focus_out(event=None):
    if entry_var.get().strip() == "":
        entry.config(fg=SEARCH_HINT)
        entry_var.set(PLACEHOLDER)

def on_key(event):
    if   event.keysym == "Return": confirm()
    elif event.keysym == "Escape": hide()
    elif event.keysym == "Down":   move_selection(1)
    elif event.keysym == "Up":     move_selection(-1)

def show_launcher():
    show_event.set()
    return False

def poll():
    global blur_ok
    if show_event.is_set():
        show_event.clear()
        entry.config(fg=SEARCH_HINT)
        entry_var.set(PLACEHOLDER)
        redraw()
        root.deiconify()
        root.lift()
        # apply blur every time we show (re-applying after hide is necessary)
        root.after(60, _reapply_blur)
        root.after(40, lambda: [on_entry_click(), entry.focus_force()])
    root.after(100, poll)

def _reapply_blur():
    global blur_ok
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    # make sure we target OUR window
    our_hwnd = ctypes.windll.user32.FindWindowW(None, "_launcher_")
    if our_hwnd:
        blur_ok = apply_blur(our_hwnd)

# ─────────────────────────────────────────────
#  BUILD WINDOW
# ─────────────────────────────────────────────
root = tk.Tk()
root.title("_launcher_")          # used by FindWindowW above
root.overrideredirect(True)
root.attributes("-topmost", True)
root.configure(bg=TRANSPARENT_KEY)  # root bg = the colour DWM sees through
root.withdraw()

# ── Apply acrylic blur once the window handle exists ──────────────────────
def _initial_blur():
    global blur_ok
    # overrideredirect windows don't show a title bar so FindWindowW won't
    # work reliably — use the HWND from winfo_id instead
    hwnd    = root.winfo_id()
    blur_ok = apply_blur(hwnd)
    if blur_ok:
        root.wm_attributes("-transparentcolor", TRANSPARENT_KEY)
    else:
        # blur not available: fall back to fully opaque dark panel
        root.configure(bg=BG)

root.after(10, _initial_blur)

# 1 px border wrapper — note: uses TRANSPARENT_KEY so the very edge is
# see-through, giving a frameless floating-panel look
border = tk.Frame(root, bg=BORDER_CLR, padx=1, pady=1)
border.pack(fill="both", expand=True)

panel = tk.Frame(border, bg=BG)
panel.pack(fill="both", expand=True)

# ── Search bar ────────────────────────────────────────────────────────────
search_frame = tk.Frame(panel, bg=BG, height=SEARCH_H)
search_frame.pack(fill="x")
search_frame.pack_propagate(False)

tk.Label(search_frame, text="⌕", font=("Segoe UI", 18), bg=BG, fg="#505050").pack(
    side="left", padx=(18, 6))

entry_var = tk.StringVar()
entry_var.trace_add("write", update_list)

entry = tk.Entry(
    search_frame,
    textvariable=entry_var,
    font=FONT_SEARCH,
    bg=BG, fg=SEARCH_HINT,
    insertbackground=CARET_CLR,
    relief="flat", bd=0, highlightthickness=0,
)
entry.pack(side="left", fill="both", expand=True)
entry.bind("<KeyPress>",  on_key)
entry.bind("<FocusIn>",   on_entry_click)
entry.bind("<FocusOut>",  on_entry_focus_out)

close_btn = tk.Label(search_frame, text="✕", font=("Segoe UI", 11),
                     bg=BG, fg="#404040", cursor="hand2", padx=16)
close_btn.pack(side="right")
close_btn.bind("<Button-1>", hide)
close_btn.bind("<Enter>",    lambda e: close_btn.config(fg="#aaaaaa"))
close_btn.bind("<Leave>",    lambda e: close_btn.config(fg="#404040"))

# ── Divider ───────────────────────────────────────────────────────────────
tk.Frame(panel, bg=BORDER_CLR, height=1).pack(fill="x")

# ── Results ───────────────────────────────────────────────────────────────
list_frame = tk.Frame(panel, bg=BG)
list_frame.pack(fill="x")

# ── Init ──────────────────────────────────────────────────────────────────
entry_var.set(PLACEHOLDER)

if ICONS_AVAILABLE:
    preload_icons_async(list(COMMANDS.keys())[:30])

keyboard.add_hotkey(HOTKEY, show_launcher, suppress=True)
root.after(100, poll)

print(f"Launcher ready — press {HOTKEY}")
root.mainloop()