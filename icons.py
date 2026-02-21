import os
import ctypes
import ctypes.wintypes
from threading import Thread

try:
    import win32ui, win32gui, win32con, win32api
    import win32com.client
    from PIL import Image, ImageTk
    ICONS_AVAILABLE = True
except ImportError:
    ICONS_AVAILABLE = False
    print("[launcher] pip install pywin32 pillow  → to get real app icons")

_icon_cache = {}
_shell = None

# shortcut res (.lnk)
def _get_shell():
    global _shell
    if _shell is None and ICONS_AVAILABLE:
        try:
            _shell = win32com.client.Dispatch("WScript.Shell")
        except Exception:
            pass
    return _shell


def _resolve_lnk(path: str) -> str:
    """Resolve .lnk to target exe or icon location."""
    try:
        sh = _get_shell()
        if sh:
            sc = sh.CreateShortCut(path)

            if sc.TargetPath and os.path.exists(sc.TargetPath):
                return sc.TargetPath
            if sc.IconLocation:
                icon_path = sc.IconLocation.split(",")[0]
                if os.path.exists(icon_path):
                    return icon_path
            if sc.Arguments:
                return sc.Arguments
    except Exception:
        pass

    return path


def _clean_icon_path(path: str):
    if not path:
        return path

    if "," in path:
        path = path.split(",")[0]

    return path.strip('"')


def _hicon_to_pil(hicon: int, size: int):
    screen_dc = win32gui.GetDC(0)
    hdc = win32ui.CreateDCFromHandle(screen_dc)
    mem_dc = hdc.CreateCompatibleDC()

    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(hdc, size, size)
    old = mem_dc.SelectObject(bmp)

    mem_dc.FillSolidRect((0, 0, size, size), 0x00000000)

    win32gui.DrawIconEx(
        mem_dc.GetSafeHdc(),
        0, 0,
        hicon,
        size, size,
        0, None,
        win32con.DI_NORMAL,
    )

    info = bmp.GetInfo()
    bits = bmp.GetBitmapBits(True)

    mem_dc.SelectObject(old)
    mem_dc.DeleteDC()
    hdc.DeleteDC()
    win32gui.ReleaseDC(0, screen_dc)
    win32gui.DestroyIcon(hicon)

    return Image.frombuffer(
        "RGBA",
        (info["bmWidth"], info["bmHeight"]),
        bits,
        "raw",
        "BGRA",
        0,
        1,
    )

#extraction ways
def _via_shgetfileinfo(path: str, size: int):
    try:
        SHGFI_ICON = 0x100
        SHGFI_LARGEICON = 0x000
        SHGFI_SMALLICON = 0x001

        flags = SHGFI_ICON | (SHGFI_LARGEICON if size >= 32 else SHGFI_SMALLICON)

        ret = win32api.SHGetFileInfo(path, 0, flags)
        hicon = ret[0]

        if not hicon:
            return None

        return _hicon_to_pil(hicon, size)
    except Exception:
        return None


def _via_extracticonex(path: str, size: int):
    try:
        target = _resolve_lnk(path) if path.lower().endswith(".lnk") else path
        target = _clean_icon_path(target)

        if not os.path.exists(target):
            return None

        large, small = win32gui.ExtractIconEx(target, 0, 1)
        wanted, other = (large, small) if size >= 32 else (small, large)

        for h in other:
            if h:
                win32gui.DestroyIcon(h)

        if not wanted or not wanted[0]:
            return None

        return _hicon_to_pil(wanted[0], size)
    except Exception:
        return None


def _via_private(path: str, size: int):
    try:
        target = _resolve_lnk(path) if path.lower().endswith(".lnk") else path
        target = _clean_icon_path(target)

        if not os.path.exists(target):
            return None

        hicon = ctypes.wintypes.HICON()
        hicon_i = ctypes.wintypes.UINT()

        n = ctypes.windll.user32.PrivateExtractIconsW(
            target,
            0,
            size,
            size,
            ctypes.byref(hicon),
            ctypes.byref(hicon_i),
            1,
            0,
        )

        if n == 0 or not hicon.value:
            return None

        return _hicon_to_pil(hicon.value, size)
    except Exception:
        return None

#default icons
def _get_default_icon(size: int):
    try:
        SHGFI_ICON = 0x100
        SHGFI_USEFILEATTRIBUTES = 0x10
        FILE_ATTRIBUTE_NORMAL = 0x80

        ret = win32api.SHGetFileInfo(
            ".exe",
            FILE_ATTRIBUTE_NORMAL,
            SHGFI_ICON | SHGFI_USEFILEATTRIBUTES,
        )

        return _hicon_to_pil(ret[0], size)
    except Exception:
        return None

#master extraction function
def _extract_icon(cmd: str, size: int = 32):
    if not cmd:
        return None
    if cmd.startswith("explorer shell:AppsFolder\\"):
        try:
            shell_path = cmd.replace("explorer ", "")
            img = _via_shgetfileinfo(shell_path, size)
            if img:
                return img
        except Exception:
            pass

    for method in (_via_shgetfileinfo, _via_extracticonex, _via_private):
        try:
            img = method(cmd, size)
            if img is not None:
                return img
        except Exception:
            continue
    return _get_default_icon(size)

def get_icon(name: str, commands: dict, size: int = 22):
    if not ICONS_AVAILABLE:
        return None

    if name in _icon_cache:
        return _icon_cache[name]

    cmd = commands.get(name, "")
    img = _extract_icon(cmd, size * 2)

    photo = None
    if img:
        img = img.resize((size, size), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)

    _icon_cache[name] = photo
    return photo


def preload_icons_async(names: list, commands: dict):
    if not ICONS_AVAILABLE:
        return

    def worker():
        for n in names:
            get_icon(n, commands)

    Thread(target=worker, daemon=True).start()