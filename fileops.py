import os
import shutil
import re

FILE_COMMANDS = [
    {
        "id":       "newfolder",
        "aliases":  ["?newfolder", "?new", "?mkdir"],
        "syntax":   "?newfolder:<path>",
        "example":  "?newfolder:C:\\Users\\me\\Desktop\\MyFolder",
        "desc":     "Create a new folder",
        "icon":     "📁",
    },
    {
        "id":       "delete",
        "aliases":  ["?delete", "?del", "?remove", "?rm"],
        "syntax":   "?delete:<path>",
        "example":  "?delete:C:\\Users\\me\\Desktop\\old.txt",
        "desc":     "Delete a file or folder",
        "icon":     "🗑️",
    },
    {
        "id":       "rename",
        "aliases":  ["?rename", "?ren", "?mv"],
        "syntax":   "?rename:<path>|<new name or full path>",
        "example":  "?rename:C:\\Users\\me\\old.txt|new.txt",
        "desc":     "Rename or move a file / folder",
        "icon":     "✏️",
    },
]

def parse_file_command(text: str) -> "dict | None":
    t = text.strip()

    if not t.startswith("?"):
        return None

    if t == "?":
        return {"state": "help"}

    matched_cmd = None
    for cmd in FILE_COMMANDS:
        for alias in cmd["aliases"]:
            if t.lower().startswith(alias.lower()):
                matched_cmd = cmd
                break
        if matched_cmd:
            break

    if not matched_cmd:
        return {
            "state":   "error",
            "message": f'Unknown command "{t.split(":")[0]}". Type ? to see all commands.',
            "icon":    "❓",
        }
    colon_idx = t.find(":")
    if colon_idx == -1 or colon_idx == len(t) - 1:
        # no args - show hint
        return {
            "state":  "hint",
            "id":     matched_cmd["id"],
            "icon":   matched_cmd["icon"],
            "syntax": matched_cmd["syntax"],
            "desc":   matched_cmd["desc"],
        }

    args_raw = t[colon_idx + 1:].strip()
    #new folder
    if matched_cmd["id"] == "newfolder":
        path = os.path.expandvars(args_raw)
        if os.path.exists(path):
            return {
                "state":   "error",
                "id":      "newfolder",
                "icon":    matched_cmd["icon"],
                "message": f'Already exists: {path}',
            }
        return {
            "state":  "ready",
            "id":     "newfolder",
            "icon":   matched_cmd["icon"],
            "desc":   f'Create folder: {path}',
            "args":   {"path": path},
        }
    #delete
    if matched_cmd["id"] == "delete":
        path = os.path.expandvars(args_raw)
        if not os.path.exists(path):
            return {
                "state":   "error",
                "id":      "delete",
                "icon":    matched_cmd["icon"],
                "message": f'Not found: {path}',
            }
        kind = "folder" if os.path.isdir(path) else "file"
        return {
            "state":  "ready",
            "id":     "delete",
            "icon":   matched_cmd["icon"],
            "desc":   f'Delete {kind}: {path}',
            "args":   {"path": path, "kind": kind},
        }
    #rename
    if matched_cmd["id"] == "rename":
        if "|" not in args_raw:
            return {
                "state":  "hint",
                "id":     "rename",
                "icon":   matched_cmd["icon"],
                "syntax": matched_cmd["syntax"],
                "desc":   "Add | then the new name  e.g.  ?rename:C:\\old.txt|new.txt",
            }
        src_raw, dst_raw = args_raw.split("|", 1)
        src = os.path.expandvars(src_raw.strip())
        dst_raw = dst_raw.strip()

        if not os.path.exists(src):
            return {
                "state":   "error",
                "id":      "rename",
                "icon":    matched_cmd["icon"],
                "message": f'Source not found: {src}',
            }
        if not os.path.dirname(dst_raw):
            dst = os.path.join(os.path.dirname(src), dst_raw)
        else:
            dst = os.path.expandvars(dst_raw)

        return {
            "state":  "ready",
            "id":     "rename",
            "icon":   matched_cmd["icon"],
            "desc":   f'Rename: {os.path.basename(src)} → {os.path.basename(dst)}',
            "args":   {"src": src, "dst": dst},
        }

    return None
import ctypes

_shell32 = ctypes.windll.shell32

SHCNE_RENAMEITEM   = 0x00000001
SHCNE_DELETE       = 0x00000002
SHCNE_MKDIR        = 0x00000008
SHCNE_RMDIR        = 0x00000010
SHCNE_RENAMEFOLDER = 0x00020000
SHCNF_PATHW        = 0x0005


def _notify(event: int, path1: str, path2: str = None):
    p1 = ctypes.c_wchar_p(path1)
    p2 = ctypes.c_wchar_p(path2) if path2 else None
    _shell32.SHChangeNotify(event, SHCNF_PATHW, p1, p2)


def _notify_shell_mkdir(path: str):
    _notify(SHCNE_MKDIR, path)


def _notify_shell_delete(path: str):
    event = SHCNE_RMDIR if not os.path.exists(path) and os.sep in path else SHCNE_DELETE
    _notify(SHCNE_DELETE, path)
    _notify(SHCNE_RMDIR,  path)


def _notify_shell_rename(src: str, dst: str):
    if os.path.isdir(dst):
        _notify(SHCNE_RENAMEFOLDER, src, dst)
    else:
        _notify(SHCNE_RENAMEITEM, src, dst)


def execute_file_command(parsed: dict) -> "tuple[bool, str]":
    if parsed.get("state") != "ready":
        return False, "Command not ready"

    cmd_id = parsed["id"]
    args   = parsed.get("args", {})

    try:
        if cmd_id == "newfolder":
            os.makedirs(args["path"], exist_ok=False)
            _notify_shell_mkdir(args["path"])
            return True, f'Created: {args["path"]}'

        if cmd_id == "delete":
            path = args["path"]
            if args["kind"] == "folder":
                shutil.rmtree(path)
            else:
                os.remove(path)
            _notify_shell_delete(path)
            return True, f'Deleted: {path}'

        if cmd_id == "rename":
            os.rename(args["src"], args["dst"])
            _notify_shell_rename(args["src"], args["dst"])
            return True, f'Renamed to: {os.path.basename(args["dst"])}'

    except PermissionError:
        return False, "Permission denied"
    except FileExistsError:
        return False, f'"{os.path.basename(args.get("dst", ""))}" already exists'
    except Exception as e:
        return False, str(e)

    return False, "Unknown command"