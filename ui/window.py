import tkinter as tk
import keyboard

from config import (
    TRANSPARENT_KEY, BG, BORDER_CLR,
    SEARCH_FG, SEARCH_HINT, CARET_CLR,
    FONT_SEARCH, FONT_SUB,
    NO_RES_FG, PLACEHOLDER,
    WIDTH, SEARCH_H, ROW_H, MAX_ROWS,
    ICON_SIZE,
)
from matcher import get_matches
from launcher_core import launch
from blur import apply_blur
from icons import preload_icons_async
from fileops import parse_file_command, execute_file_command, FILE_COMMANDS
from flows import load_flows, search_flows, run_flow, open_flows_file
from .rows import draw_row, draw_web_search_row, draw_file_command_row, draw_flow_row, draw_flow_header
from . import state


def run_ui(commands: dict, hotkey: str):

    # ── Build window ──────────────────────────────────────────────────────
    root = tk.Tk()
    root.title("_pycast_")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg=TRANSPARENT_KEY)
    root.withdraw()

    def _apply_blur():
        hwnd = root.winfo_id()
        ok   = apply_blur(hwnd)
        if ok:
            root.wm_attributes("-transparentcolor", TRANSPARENT_KEY)
        else:
            root.configure(bg=BG)
        print(f"[blur] {'acrylic enabled' if ok else 'not supported on this build'}")

    root.after(10, _apply_blur)

    # ── Layout ────────────────────────────────────────────────────────────
    border = tk.Frame(root, bg=BORDER_CLR, padx=1, pady=1)
    border.pack(fill="both", expand=True)

    panel = tk.Frame(border, bg=BG)
    panel.pack(fill="both", expand=True)

    search_frame = tk.Frame(panel, bg=BG, height=SEARCH_H)
    search_frame.pack(fill="x")
    search_frame.pack_propagate(False)

    tk.Label(
        search_frame, text="⌕",
        font=("Segoe UI", 18), bg=BG, fg="#505050",
    ).pack(side="left", padx=(18, 6))

    entry_var = tk.StringVar()

    entry = tk.Entry(
        search_frame,
        textvariable=entry_var,
        font=FONT_SEARCH,
        bg=BG, fg=SEARCH_HINT,
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

    # ── Geometry ──────────────────────────────────────────────────────────
    def set_geometry(rows: int):
        h  = SEARCH_H
        if rows > 0:
            h += 1 + rows * ROW_H + 8
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{WIDTH}x{h}+{(sw - WIDTH)//2}+{sh//3}")

    # ── Load flows ────────────────────────────────────────────────────────
    flows = load_flows()

    def reload_flows():
        nonlocal flows
        flows = load_flows()
        show_feedback(f"✓ {len(flows)} flows reloaded", ok=True)

    # ── Feedback label (shown briefly after file ops) ──────────────────────
    _feedback_job  = [None]
    _in_feedback   = [False]

    def show_feedback(msg: str, ok: bool = True):
        _in_feedback[0] = True
        colour = "#50c878" if ok else "#e05050"
        entry.config(fg=colour)
        entry_var.set(msg)
        for w in list_frame.winfo_children():
            w.destroy()
        set_geometry(rows=0)
        if _feedback_job[0]:
            root.after_cancel(_feedback_job[0])
        def _reset():
            _in_feedback[0] = False
            hide()
        _feedback_job[0] = root.after(2000, _reset)

    # ── Redraw ────────────────────────────────────────────────────────────
    def redraw():
        for w in list_frame.winfo_children():
            w.destroy()

        raw       = entry_var.get()
        q         = raw.strip()
        has_query = bool(q and q != PLACEHOLDER)

        # ── Flow mode  (prefix >) ─────────────────────────────────────────
        if q.startswith(">"):
            flow_query   = q[1:].strip()
            flow_results = search_flows(flow_query, flows)

            # header row
            draw_flow_header(list_frame, _edit_flows_file)

            if not flow_results:
                tk.Label(list_frame, text="No flows found — type ? to see file commands",
                         font=FONT_SUB, bg=BG, fg="#3d2d5a", anchor="w").pack(
                             fill="x", padx=20, pady=10)
                set_geometry(rows=2)
                return

            visible = min(len(flow_results), MAX_ROWS)
            for i, flow in enumerate(flow_results[:MAX_ROWS]):
                draw_flow_row(
                    list_frame, i, flow,
                    i == state.selected,
                    _execute_flow,
                    _edit_flows_file,
                )
            # header counts as 0.6 of a row visually
            set_geometry(rows=visible + 1)
            return

        # ── File command mode  (prefix ?) ────────────────────────────────
        if q.startswith("?"):
            parsed = parse_file_command(q)
            if parsed:
                if parsed["state"] == "help":
                    draw_file_command_row(list_frame, parsed, False, lambda: None)
                    set_geometry(rows=len(FILE_COMMANDS))
                else:
                    draw_file_command_row(list_frame, parsed, True, _run_file_command)
                    set_geometry(rows=1)
            return

        # ── Normal app search ─────────────────────────────────────────────
        n = min(len(state.matches), MAX_ROWS)

        if n == 0 and not has_query:
            set_geometry(rows=0)
            return

        for i, name in enumerate(state.matches[:MAX_ROWS]):
            draw_row(list_frame, i, name, i == state.selected, commands, confirm)

        if has_query:
            web_sel = (state.selected == n)
            draw_web_search_row(list_frame, q, web_sel, web_search)

        total = n + (1 if has_query else 0)
        set_geometry(rows=max(total, 0))

        if n > 0:
            preload_icons_async(state.matches[:MAX_ROWS], commands)

    # ── List update ───────────────────────────────────────────────────────
    def update_list(*_):
        if _in_feedback[0]:
            return
        text = entry_var.get()
        if text == PLACEHOLDER or text == "":
            state.matches  = []
            state.selected = 0
            redraw()
            return
        # flow and file command modes skip fuzzy app matching
        if text.strip().startswith(">") or text.strip().startswith("?"):
            state.matches  = []
            state.selected = 0
            redraw()
            return
        state.matches  = get_matches(text, commands)
        state.selected = 0
        redraw()

    entry_var.trace_add("write", update_list)

    # ── Placeholder ───────────────────────────────────────────────────────
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

    # ── Actions ───────────────────────────────────────────────────────────
    def _execute_flow(flow: dict):
        """Run a flow then hide the launcher."""
        import threading
        name = flow.get("name", "flow")
        show_feedback(f"⚡ Running '{name}'…", ok=True)
        # run in a thread so UI doesn't freeze during the step delays
        threading.Thread(target=run_flow, args=(flow, commands), daemon=True).start()

    def _edit_flows_file():
        """Open flows.json in the user's default editor."""
        open_flows_file()
        hide()

    def _run_file_command():
        q      = entry_var.get().strip()
        parsed = parse_file_command(q)
        if not parsed or parsed["state"] != "ready":
            return
        ok, msg = execute_file_command(parsed)
        print(f"[fileops] {'✓' if ok else '✗'} {msg}")
        show_feedback(("✓ " if ok else "✗ ") + msg, ok=ok)

    def web_search(query: str = None):
        import subprocess
        q = query or entry_var.get().strip()
        if q and q != PLACEHOLDER:
            subprocess.Popen(f"start https://www.google.com/search?q={q}", shell=True)
        hide()

    def confirm(name=None):
        q         = entry_var.get().strip()
        has_query = bool(q and q != PLACEHOLDER)

        # flow mode — Enter runs selected flow
        if q.startswith(">"):
            flow_query   = q[1:].strip()
            flow_results = search_flows(flow_query, flows)
            if flow_results and state.selected < len(flow_results):
                _execute_flow(flow_results[state.selected])
            return

        # file command mode — Enter executes it
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

        # flow mode navigation
        if q.startswith(">"):
            flow_query   = q[1:].strip()
            flow_results = search_flows(flow_query, flows)
            total = min(len(flow_results), MAX_ROWS)
            if total == 0:
                return
            state.selected = (state.selected + delta) % total
            redraw()
            return

        # no arrow navigation in file command mode
        if q.startswith("?"):
            return
        n_apps = min(len(state.matches), MAX_ROWS)
        total  = n_apps + (1 if has_query else 0)
        if total == 0:
            return
        state.selected = (state.selected + delta) % total
        redraw()

    # ── Key bindings ──────────────────────────────────────────────────────
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

    # ── Global hotkey ─────────────────────────────────────────────────────
    def show_launcher():
        state.show_event.set()
        return False

    def poll():
        if state.show_event.is_set():
            state.show_event.clear()
            entry.config(fg=SEARCH_HINT)
            entry_var.set(PLACEHOLDER)
            redraw()
            root.deiconify()
            root.lift()
            root.after(40, lambda: apply_blur(root.winfo_id()))
            root.after(50, lambda: [on_focus_in(), entry.focus_force()])
        root.after(100, poll)

    keyboard.add_hotkey(hotkey, show_launcher, suppress=True)

    # ── Init ──────────────────────────────────────────────────────────────
    entry_var.set(PLACEHOLDER)
    preload_icons_async(list(commands.keys())[:30], commands)

    root.after(100, poll)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        keyboard.unhook_all()
        try:
            root.destroy()
        except Exception:
            pass