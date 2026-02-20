import os
import glob
import subprocess
from config import SCAN_DIRS, MANUAL_COMMANDS


# ─────────────────────────────────────────────
#  TRADITIONAL APPS  (.lnk from Start Menu)
# ─────────────────────────────────────────────
def scan_lnk_files() -> dict:
    found = {}
    skip  = ("uninstall", "help", "readme", "release notes", "documentation")

    for d in SCAN_DIRS:
        if not os.path.isdir(d):
            continue
        for lnk in glob.glob(os.path.join(d, "**", "*.lnk"), recursive=True):
            name = os.path.splitext(os.path.basename(lnk))[0].lower()
            if any(w in name for w in skip):
                continue
            found.setdefault(name, lnk)

    return found


# ─────────────────────────────────────────────
#  MICROSOFT STORE APPS
#
#  Store apps don't have .lnk shortcuts or .exe files you can call directly.
#  Windows registers them under a hidden virtual folder: shell:AppsFolder
#  Each app has an AppUserModelId (AUMID) like:
#      Microsoft.WindowsCalculator_8wekyb3d8bbwe!App
#  You launch them with:
#      explorer.exe shell:AppsFolder\<AUMID>
#
#  We enumerate all AUMIDs using PowerShell's Get-StartApps cmdlet which
#  returns every pinnable app — both traditional and Store — with its name
#  and AppID.
# ─────────────────────────────────────────────
def scan_store_apps() -> dict:
    """
    Run Get-StartApps via PowerShell and return {display_name: launch_cmd}.
    Launch command format:  explorer shell:AppsFolder\<AppID>
    """
    found = {}
    skip  = ("uninstall", "help", "readme", "documentation", "runtime",
             "framework", "vcredist", "redistributable", "microsoft visual c")

    try:
        ps_cmd = (
            "Get-StartApps | "
            "Select-Object Name, AppID | "
            "ConvertTo-Csv -NoTypeInformation"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print(f"[scanner] PowerShell error: {result.stderr.strip()}")
            return found

        lines = result.stdout.strip().splitlines()
        if len(lines) < 2:
            return found

        # skip CSV header ("Name","AppID")
        for line in lines[1:]:
            line = line.strip().strip('"')
            if not line:
                continue

            # CSV row:  "Display Name","AppID"
            parts = line.split('","')
            if len(parts) != 2:
                continue

            display_name = parts[0].strip('"').strip().lower()
            app_id       = parts[1].strip('"').strip()

            if not display_name or not app_id:
                continue
            if any(w in display_name for w in skip):
                continue

            # Store apps have a '!' in their AUMID; traditional apps are plain paths.
            # We only want Store apps here — .lnk scanner handles the rest.
            if "!" not in app_id:
                continue

            cmd = f"explorer shell:AppsFolder\\{app_id}"
            found.setdefault(display_name, cmd)

    except FileNotFoundError:
        print("[scanner] PowerShell not found — skipping Store app scan")
    except subprocess.TimeoutExpired:
        print("[scanner] PowerShell timed out — skipping Store app scan")
    except Exception as e:
        print(f"[scanner] Store app scan failed: {e}")

    return found


# ─────────────────────────────────────────────
#  LAUNCH HELPER  (used by launcher_core for store apps)
# ─────────────────────────────────────────────
def is_store_app(cmd: str) -> bool:
    return cmd.startswith("explorer shell:AppsFolder\\")


# ─────────────────────────────────────────────
#  BUILD FULL COMMAND TABLE
# ─────────────────────────────────────────────
def build_commands() -> dict:
    print("[scanner] scanning traditional apps...")
    table = scan_lnk_files()

    print("[scanner] scanning Microsoft Store apps...")
    store = scan_store_apps()
    print(f"[scanner] found {len(store)} Store apps")

    # merge — lnk takes priority over store if same name
    for k, v in store.items():
        table.setdefault(k, v)

    # manual commands always win
    for k, v in MANUAL_COMMANDS.items():
        table[k] = os.path.expandvars(v)

    return table