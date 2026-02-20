import subprocess
import os

try:
    import win32gui
    import win32process
    import win32con
    import win32api
    import win32com.client
    import psutil
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("[launcher] pip install pywin32 psutil  →  to enable focus-existing-window")


# ─────────────────────────────────────────────
#  RESOLVE: command  →  token for process matching
# ─────────────────────────────────────────────
_shell = None

def _get_shell():
    global _shell
    if _shell is None and WIN32_AVAILABLE:
        try:
            _shell = win32com.client.Dispatch("WScript.Shell")
        except Exception:
            pass
    return _shell


def _resolve_target(cmd: str) -> str:
    """
    Convert a command string into a search token used to find a running process.

    .lnk          → resolve shortcut → basename of target .exe
    .exe path      → basename of .exe
    Store app      → package name portion of AUMID  (e.g. "microsoft.windowscalculator")
    shell command  → first word  (e.g. "notepad")
    """
    if cmd.endswith(".lnk"):
        try:
            sh = _get_shell()
            if sh:
                sc  = sh.CreateShortCut(cmd)
                tgt = sc.TargetPath
                if tgt:
                    return os.path.basename(tgt).lower()
        except Exception:
            pass
        return ""

    if cmd.endswith(".exe"):
        return os.path.basename(cmd).lower()

    # Store apps:  "explorer shell:AppsFolder\Microsoft.WindowsCalculator_8wekyb3d8bbwe!App"
    if cmd.startswith("explorer shell:AppsFolder\\"):
        aumid = cmd.split("\\", 1)[1]       # Microsoft.WindowsCalculator_8wekyb3d8bbwe!App
        pkg   = aumid.split("!")[0]         # Microsoft.WindowsCalculator_8wekyb3d8bbwe
        return pkg.rsplit("_", 1)[0].lower()  # microsoft.windowscalculator

    # plain shell commands: notepad, explorer, etc.
    return cmd.strip().lower().split()[0]


# ─────────────────────────────────────────────
#  FIND A RUNNING INSTANCE
# ─────────────────────────────────────────────
def _find_window_for_exe(target: str) -> "int | None":
    if not WIN32_AVAILABLE:
        return None

    target     = target.lower().removesuffix(".exe")
    candidates = []

    def _enum(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        if not win32gui.GetWindowText(hwnd):
            return
        try:
            _, pid   = win32process.GetWindowThreadProcessId(hwnd)
            proc     = psutil.Process(pid)
            exe_name = proc.name().lower().removesuffix(".exe")
            exe_path = ""
            try:
                exe_path = proc.exe().lower()
            except (psutil.AccessDenied, Exception):
                pass

            if target in exe_name or target in exe_path:
                candidates.append(hwnd)
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            pass

    try:
        win32gui.EnumWindows(_enum, None)
    except Exception:
        pass

    # EnumWindows returns in Z-order → first = topmost/most recent
    return candidates[0] if candidates else None


# ─────────────────────────────────────────────
#  FOCUS AN EXISTING WINDOW
# ─────────────────────────────────────────────
def _focus_window(hwnd: int):
    """Bring hwnd to foreground, restoring if minimised."""
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

        fg = win32gui.GetForegroundWindow()
        if fg != hwnd:
            try:
                fg_tid, _ = win32process.GetWindowThreadProcessId(fg)
                our_tid   = win32api.GetCurrentThreadId()
                # AttachThreadInput lets us steal focus reliably
                win32process.AttachThreadInput(our_tid, fg_tid, True)
                win32gui.SetForegroundWindow(hwnd)
                win32process.AttachThreadInput(our_tid, fg_tid, False)
            except Exception:
                win32gui.SetForegroundWindow(hwnd)
    except Exception as e:
        print(f"[launcher] focus failed: {e}")


# ─────────────────────────────────────────────
#  PUBLIC: launch or focus
# ─────────────────────────────────────────────
def launch(name: str, commands: dict):
    if name not in commands:
        return

    cmd    = commands[name]
    target = _resolve_target(cmd)

    # ── Try to bring an existing instance to focus ────────────────────────
    if target and WIN32_AVAILABLE:
        hwnd = _find_window_for_exe(target)
        if hwnd:
            print(f"[launcher] focusing existing '{target}' (hwnd={hwnd})")
            _focus_window(hwnd)
            return

    # ── No running instance — launch fresh ───────────────────────────────
    print(f"[launcher] launching '{name}'")

    if cmd.startswith("explorer shell:AppsFolder\\"):
        # Store apps must go through explorer with shell: protocol
        subprocess.Popen(cmd, shell=True)
    elif cmd.endswith(".lnk"):
        os.startfile(cmd)
    elif cmd.startswith("start "):
        subprocess.Popen(cmd, shell=True)
    elif cmd.endswith(".exe"):
        subprocess.Popen([cmd])
    else:
        subprocess.Popen(cmd, shell=True)