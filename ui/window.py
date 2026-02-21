import tkinter as tk
import ctypes
import ctypes.wintypes
import threading
import subprocess
import signal
import sys

from config import (
    BG, BORDER_CLR,
    SEARCH_FG, SEARCH_HINT, CARET_CLR,
    FONT_SEARCH, FONT_SUB,
    NO_RES_FG, PLACEHOLDER,
    WIDTH, SEARCH_H, ROW_H, MAX_ROWS,
    ICON_SIZE,
)
from matcher import get_matches
from launcher_core import launch
from icons import preload_icons_async
from fileops import parse_file_command, execute_file_command, FILE_COMMANDS
from flows import load_flows, search_flows, run_flow, open_flows_file
from .rows import draw_row, draw_web_search_row, draw_file_command_row, draw_flow_row, draw_flow_header
from . import state

# win32 hotkey constants
MOD_ALT      = 0x0001
MOD_CTRL     = 0x0002
MOD_SHIFT    = 0x0004
MOD_WIN      = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY    = 0x0312
VK_SPACE     = 0x20
_HOTKEY_ID   = 1


def _parse_hotkey(s: str):
    mods, vk = MOD_NOREPEAT, 0
    for p in [x.strip().lower() for x in s.split("+")]:
        if p == "ctrl":    mods |= MOD_CTRL
        elif p == "alt":   mods |= MOD_ALT
        elif p == "shift": mods |= MOD_SHIFT
        elif p == "win":   mods |= MOD_WIN
        elif p == "space": vk = VK_SPACE
        elif len(p) == 1:  vk = ord(p.upper())
    return mods, vk


def run_ui(commands: dict, hotkey: str):

    root = tk.Tk()
    root.title("_pycast_")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg=BG)
    root.withdraw()

    # no expand=True — window sizes to content, not the other way round
    border = tk.Frame(root, bg=BORDER_CLR, padx=1, pady=1)
    border.pack(fill="x")

    panel = tk.Frame(border, bg=BG)
    panel.pack(fill="x")

    search_frame = tk.Frame(panel, bg=BG, height=SEARCH_H)
    search_frame.pack(fill="x")
    search_frame.pack_propagate(False)

    tk.Label(search_frame, text="⌕", font=("Segoe UI", 18), bg=BG, fg="#505050").pack(
        side="left", padx=(18, 6)
    )

    entry_var = tk.StringVar()
    entry = tk.Entry(
        search_frame, textvariable=entry_var,
        font=FONT_SEARCH, bg=BG, fg=SEARCH_HINT,
        insertbackground=CARET_CLR,
        relief="flat", bd=0, highlightthickness=0,
    )
    entry.pack(side="left", fill="both", expand=True)

    close_btn = tk.Label(
        search_frame, text="✕",
        font=("Segoe UI", 11), bg=BG, fg="#404040",
        cursor="hand2", padx=16,
    )
    close_btn.pack(side="right")

    tk.Frame(panel, bg=BORDER_CLR, height=1).pack(fill="x")

    list_frame = tk.Frame(panel, bg=BG)
    list_frame.pack(fill="x")

    # base = search bar + divider + border
    _BASE_H = SEARCH_H + 1 + 4

    def fit_to_content():
        root.update_idletasks()
        content_h = sum(w.winfo_reqheight() for w in list_frame.winfo_children())
        h  = _BASE_H + content_h
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{WIDTH}x{h}+{(sw - WIDTH)//2}+{sh//3}")

    flows = load_flows()

    _feedback_job = [None]
    _in_feedback  = [False]

    def show_feedback(msg: str, ok: bool = True):
        _in_feedback[0] = True
        entry.config(fg="#50c878" if ok else "#e05050")
        entry_var.set(msg)
        for w in list_frame.winfo_children():
            w.destroy()
        fit_to_content()
        if _feedback_job[0]:
            root.after_cancel(_feedback_job[0])
        def _reset():
            _in_feedback[0] = False
            hide()
        _feedback_job[0] = root.after(2000, _reset)

    def redraw():
        for w in list_frame.winfo_children():
            w.destroy()

        q         = entry_var.get().strip()
        has_query = bool(q and q != PLACEHOLDER)

        if q.startswith(">"):
            flow_results = search_flows(q[1:].strip(), flows)
            draw_flow_header(list_frame, _edit_flows_file)
            if not flow_results:
                f = tk.Frame(list_frame, bg=BG, height=ROW_H)
                f.pack(fill="x")
                f.pack_propagate(False)
                tk.Label(f, text="No flows found  —  edit flows.json to add one",
                         font=FONT_SUB, bg=BG, fg="#3d2d5a", anchor="w").pack(
                             side="left", padx=20)
            else:
                for i, flow in enumerate(flow_results[:MAX_ROWS]):
                    draw_flow_row(list_frame, i, flow, i == state.selected,
                                  _execute_flow, _edit_flows_file)
            fit_to_content()
            return

        if q.startswith("?"):
            parsed = parse_file_command(q)
            if parsed:
                if parsed["state"] == "help":
                    draw_file_command_row(list_frame, parsed, False, lambda: None)
                else:
                    draw_file_command_row(list_frame, parsed, True, _run_file_command)
            fit_to_content()
            return

        if not has_query:
            fit_to_content()
            return

        n = min(len(state.matches), MAX_ROWS)
        for i, name in enumerate(state.matches[:MAX_ROWS]):
            draw_row(list_frame, i, name, i == state.selected, commands, confirm)

        draw_web_search_row(list_frame, q, state.selected == n, web_search)
        fit_to_content()

        if n > 0:
            preload_icons_async(state.matches[:MAX_ROWS], commands)

    def update_list(*_):
        if _in_feedback[0]:
            return
        text = entry_var.get()
        if text == PLACEHOLDER or text == "":
            state.matches  = []
            state.selected = 0
            redraw()
            return
        if text.strip().startswith(">") or text.strip().startswith("?"):
            state.matches  = []
            state.selected = 0
            redraw()
            return
        state.matches  = get_matches(text, commands)
        state.selected = 0
        redraw()

    entry_var.trace_add("write", update_list)

    def on_focus_in(e=None):
        if entry_var.get() == PLACEHOLDER:
            entry.config(fg=SEARCH_FG)
            entry_var.set("")

    def on_focus_out(e=None):
        if entry_var.get().strip() == "":
            entry.config(fg=SEARCH_HINT)
            entry_var.set(PLACEHOLDER)

    entry.bind("<FocusIn>",  on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)

    def _execute_flow(flow: dict):
        show_feedback(f"⚡ Running '{flow.get('name', 'flow')}'…", ok=True)
        threading.Thread(target=run_flow, args=(flow, commands), daemon=True).start()

    def _edit_flows_file():
        open_flows_file()
        hide()

    def _run_file_command():
        q      = entry_var.get().strip()
        parsed = parse_file_command(q)
        if not parsed or parsed["state"] != "ready":
            return
        ok, msg = execute_file_command(parsed)
        show_feedback(("✓ " if ok else "✗ ") + msg, ok=ok)

    def web_search(query: str = None):
        q = query or entry_var.get().strip()
        if q and q != PLACEHOLDER:
            subprocess.Popen(f"start https://www.google.com/search?q={q}", shell=True)
        hide()

    def confirm(name=None):
        q         = entry_var.get().strip()
        has_query = bool(q and q != PLACEHOLDER)

        if q.startswith(">"):
            flow_results = search_flows(q[1:].strip(), flows)
            if flow_results and state.selected < len(flow_results):
                _execute_flow(flow_results[state.selected])
            return

        if q.startswith("?"):
            _run_file_command()
            return

        n_apps = min(len(state.matches), MAX_ROWS)
        if name is None:
            if has_query and state.selected == n_apps:
                web_search(q)
                return
            name = state.matches[state.selected] if state.matches else None

        if name:
            launch(name, commands)
        hide()

    def hide(e=None):
        entry_var.set(PLACEHOLDER)
        entry.config(fg=SEARCH_HINT)
        root.withdraw()

    def move_selection(delta: int):
        q         = entry_var.get().strip()
        has_query = bool(q and q != PLACEHOLDER)

        if q.startswith(">"):
            flow_results = search_flows(q[1:].strip(), flows)
            total = min(len(flow_results), MAX_ROWS)
            if total == 0: return
            state.selected = (state.selected + delta) % total
            redraw()
            return

        if q.startswith("?"):
            return

        n_apps = min(len(state.matches), MAX_ROWS)
        total  = n_apps + (1 if has_query else 0)
        if total == 0: return
        state.selected = (state.selected + delta) % total
        redraw()

    def on_key(e):
        if   e.keysym == "Return": confirm()
        elif e.keysym == "Escape": hide()
        elif e.keysym == "Down":   move_selection(1)
        elif e.keysym == "Up":     move_selection(-1)
        elif e.keysym == "Tab":
            web_search()
            return "break"

    entry.bind("<KeyPress>", on_key)
    close_btn.bind("<Button-1>", hide)
    close_btn.bind("<Enter>",    lambda e: close_btn.config(fg="#aaaaaa"))
    close_btn.bind("<Leave>",    lambda e: close_btn.config(fg="#404040"))

    # RegisterHotKey doesn't need admin, unlike keyboard lib with suppress=True
    mods, vk = _parse_hotkey(hotkey)
    _hotkey_registered = [False]

    def _show_window():
        entry.config(fg=SEARCH_HINT)
        entry_var.set(PLACEHOLDER)
        redraw()
        root.deiconify()
        root.lift()
        root.after(50, lambda: [on_focus_in(), entry.focus_force()])

    def _hotkey_thread():
        user32 = ctypes.windll.user32
        ok = user32.RegisterHotKey(None, _HOTKEY_ID, mods, vk)
        if not ok:
            ok = user32.RegisterHotKey(None, _HOTKEY_ID, mods & ~MOD_NOREPEAT, vk)
        if not ok:
            print(f"[hotkey] failed to register {hotkey} — already in use?")
            return
        _hotkey_registered[0] = True
        print(f"[hotkey] registered {hotkey}")
        msg = ctypes.wintypes.MSG()
        while True:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0 or ret == -1:
                break
            if msg.message == WM_HOTKEY and msg.wParam == _HOTKEY_ID:
                root.after(0, _show_window)
        user32.UnregisterHotKey(None, _HOTKEY_ID)

    t = threading.Thread(target=_hotkey_thread, daemon=True)
    t.start()

    def _quit(sig=None, frame=None):
        # unblock GetMessageW in the hotkey thread, then stop tkinter
        if _hotkey_registered[0]:
            ctypes.windll.user32.PostThreadMessageW(t.ident, 0x0012, 0, 0)
        try:
            root.quit()
        except Exception:
            pass

    signal.signal(signal.SIGINT, _quit)

    entry_var.set(PLACEHOLDER)
    preload_icons_async(list(commands.keys())[:30], commands)

    try:
        root.mainloop()
    finally:
        _quit()
        try:
            root.destroy()
        except Exception:
            pass