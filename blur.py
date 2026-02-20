import ctypes
import ctypes.wintypes

_ACCENT_ENABLE_BLURBEHIND        = 3
_ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
_WCA_ACCENT_POLICY               = 19


class _ACCENTPOLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState",   ctypes.c_uint),
        ("AccentFlags",   ctypes.c_uint),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId",   ctypes.c_uint),
    ]


class _WINCOMPATTRDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("pData",     ctypes.c_void_p),
        ("DataSize",  ctypes.wintypes.ULONG),
    ]


def apply_blur(hwnd: int, dark: bool = True) -> bool:
    """Apply Windows Acrylic blur to hwnd. Returns True on success."""
    try:
        user32 = ctypes.windll.user32
        tint   = 0xCC1A1A1A if dark else 0xCCF5F5F5

        policy              = _ACCENTPOLICY()
        policy.AccentState  = _ACCENT_ENABLE_ACRYLICBLURBEHIND
        policy.AccentFlags  = 2
        policy.GradientColor = tint

        data           = _WINCOMPATTRDATA()
        data.Attribute = _WCA_ACCENT_POLICY
        data.pData     = ctypes.cast(ctypes.pointer(policy), ctypes.c_void_p)
        data.DataSize  = ctypes.sizeof(policy)

        if user32.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data)):
            return True

        # Fallback: plain blur (Win10 RTM–1607)
        policy.AccentState = _ACCENT_ENABLE_BLURBEHIND
        return bool(user32.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data)))

    except Exception:
        return False