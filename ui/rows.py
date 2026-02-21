import tkinter as tk
import os

from config import (
    ROW_BG, ROW_HOV_BG, ROW_SEL_BG, ROW_SEL_BAR,
    ROW_FG, ROW_SEL_FG, ROW_SUB_FG, ROW_SEL_SUB,
    DIVIDER_CLR, ICON_BG, ICON_FG,
    FONT_NAME, FONT_SEL, FONT_SUB,
    ROW_H, ICON_SIZE,
)
from icons import get_icon
from . import state

WEB_BG     = "#161616"
WEB_HOV_BG = "#1e2030"
WEB_SEL_BG = "#0f2040"
WEB_FG     = "#7aaeee"
WEB_SEL_FG = "#a0c8ff"
WEB_SUB_FG = "#3a3a3a"

FILE_CMD_BG     = "#131820"
FILE_CMD_HOV_BG = "#1a2030"
FILE_CMD_SEL_BG = "#0d2137"
FILE_CMD_FG     = "#60a8e0"
FILE_CMD_SEL_FG = "#90c8ff"
FILE_CMD_SUB_FG = "#384858"
FILE_CMD_ERR_FG = "#e05050"

FLOW_BG     = "#13111f"
FLOW_HOV_BG = "#1a1730"
FLOW_SEL_BG = "#1e1040"
FLOW_BAR    = "#a855f7"
FLOW_FG     = "#c084fc"
FLOW_SEL_FG = "#e9d5ff"
FLOW_SUB_FG = "#483d6b"
FLOW_ICON   = "⚡"


def draw_row(parent, idx, name, is_sel, commands, on_click):
    bg   = ROW_SEL_BG if is_sel else ROW_BG
    fg   = ROW_SEL_FG if is_sel else ROW_FG
    sfg  = ROW_SEL_SUB if is_sel else ROW_SUB_FG
    font = FONT_SEL if is_sel else FONT_NAME

    outer = tk.Frame(parent, bg=bg, height=ROW_H)
    outer.pack(fill="x")
    outer.pack_propagate(False)

    tk.Frame(outer, bg=ROW_SEL_BAR if is_sel else bg, width=3).pack(side="left", fill="y")

    inner = tk.Frame(outer, bg=bg)
    inner.pack(side="left", fill="both", expand=True)

    photo = get_icon(name, commands)
    if photo:
        lbl = tk.Label(inner, image=photo, bg=bg, bd=0)
        lbl.image = photo
        lbl.place(x=12, rely=0.5, anchor="w")
    else:
        box = tk.Frame(inner, bg=ICON_BG, width=ICON_SIZE, height=ICON_SIZE)
        box.place(x=12, rely=0.5, anchor="w")
        tk.Label(box, text=name[0].upper(), font=("Segoe UI Semibold", 8),
                 bg=ICON_BG, fg=ICON_FG).place(relx=0.5, rely=0.5, anchor="center")

    TEXT_X = 12 + ICON_SIZE + 10

    tk.Label(inner, text=name, font=font, bg=bg, fg=fg, anchor="w").place(
        x=TEXT_X, rely=0.5, anchor="w")

    cmd  = commands[name]
    hint = os.path.basename(cmd) if os.path.isabs(cmd) else cmd
    if len(hint) > 38:
        hint = "…" + hint[-36:]
    tk.Label(inner, text=hint, font=FONT_SUB, bg=bg, fg=sfg, anchor="e").place(
        relx=1.0, x=-14, rely=0.5, anchor="e")

    if not is_sel:
        tk.Frame(outer, bg=DIVIDER_CLR, height=1).place(
            relx=0, rely=1.0, anchor="sw", relwidth=1.0)

    all_w = [outer, inner] + list(inner.winfo_children())

    def on_enter(e, o=outer, f=inner, i=idx):
        if i != state.selected:
            for w in (o, f): w.config(bg=ROW_HOV_BG)
            for c in f.winfo_children(): c.config(bg=ROW_HOV_BG)

    def on_leave(e, o=outer, f=inner, i=idx):
        if i != state.selected:
            for w in (o, f): w.config(bg=ROW_BG)
            for c in f.winfo_children(): c.config(bg=ROW_BG)

    for w in all_w:
        w.bind("<Button-1>", lambda e, n=name: on_click(n))
        w.bind("<Enter>",    on_enter)
        w.bind("<Leave>",    on_leave)


def draw_web_search_row(parent, query: str, is_sel: bool, on_click):
    bg   = WEB_SEL_BG if is_sel else WEB_BG
    fg   = WEB_SEL_FG if is_sel else WEB_FG
    sfg  = WEB_SUB_FG

    tk.Frame(parent, bg=DIVIDER_CLR, height=1).pack(fill="x")

    outer = tk.Frame(parent, bg=bg, height=ROW_H)
    outer.pack(fill="x")
    outer.pack_propagate(False)

    tk.Frame(outer, bg=ROW_SEL_BAR if is_sel else bg, width=3).pack(side="left", fill="y")

    inner = tk.Frame(outer, bg=bg)
    inner.pack(side="left", fill="both", expand=True)

    tk.Label(inner, text="🌐", font=("Segoe UI", 13), bg=bg, fg=fg).place(
        x=10, rely=0.5, anchor="w")

    TEXT_X = 12 + ICON_SIZE + 10
    short_q = query if len(query) <= 40 else query[:38] + "…"

    tk.Label(inner, text=f'Search Google for "{short_q}"',
             font=FONT_NAME, bg=bg, fg=fg, anchor="w").place(x=TEXT_X, rely=0.5, anchor="w")

    tk.Label(inner, text="Tab", font=FONT_SUB, bg=bg, fg=sfg, anchor="e").place(
        relx=1.0, x=-14, rely=0.5, anchor="e")

    all_w = [outer, inner] + list(inner.winfo_children())

    def on_enter(e, o=outer, f=inner):
        if not is_sel:
            for w in (o, f): w.config(bg=WEB_HOV_BG)
            for c in f.winfo_children(): c.config(bg=WEB_HOV_BG)

    def on_leave(e, o=outer, f=inner):
        if not is_sel:
            for w in (o, f): w.config(bg=WEB_BG)
            for c in f.winfo_children(): c.config(bg=WEB_BG)

    for w in all_w:
        w.bind("<Button-1>", lambda e: on_click(query))
        w.bind("<Enter>",    on_enter)
        w.bind("<Leave>",    on_leave)


def draw_file_command_row(parent, parsed: dict, is_sel: bool, on_execute):
    state_val = parsed.get("state", "error")
    bg   = FILE_CMD_SEL_BG if is_sel else FILE_CMD_BG
    fg   = FILE_CMD_SEL_FG if is_sel else FILE_CMD_FG
    sfg  = FILE_CMD_SUB_FG

    tk.Frame(parent, bg=DIVIDER_CLR, height=1).pack(fill="x")

    if state_val == "help":
        _draw_help_rows(parent)
        return

    outer = tk.Frame(parent, bg=bg, height=ROW_H)
    outer.pack(fill="x")
    outer.pack_propagate(False)

    bar = ROW_SEL_BAR if is_sel else (FILE_CMD_ERR_FG if state_val == "error" else FILE_CMD_FG)
    tk.Frame(outer, bg=bar, width=3).pack(side="left", fill="y")

    inner = tk.Frame(outer, bg=bg)
    inner.pack(side="left", fill="both", expand=True)

    tk.Label(inner, text=parsed.get("icon", "📁"), font=("Segoe UI", 13),
             bg=bg, fg=fg).place(x=10, rely=0.5, anchor="w")

    TEXT_X = 12 + ICON_SIZE + 10

    if state_val == "error":
        tk.Label(inner, text=parsed.get("message", "Error"), font=FONT_NAME,
                 bg=bg, fg=FILE_CMD_ERR_FG, anchor="w").place(x=TEXT_X, rely=0.5, anchor="w")

    elif state_val == "hint":
        tk.Label(inner, text=parsed.get("syntax", ""), font=FONT_SEL,
                 bg=bg, fg=fg, anchor="w").place(x=TEXT_X, rely=0.5, anchor="w")
        tk.Label(inner, text=parsed.get("desc", ""), font=FONT_SUB,
                 bg=bg, fg=sfg, anchor="e").place(relx=1.0, x=-14, rely=0.5, anchor="e")

    elif state_val == "ready":
        tk.Label(inner, text=parsed.get("desc", ""), font=FONT_NAME,
                 bg=bg, fg=fg, anchor="w").place(x=TEXT_X, rely=0.5, anchor="w")
        tk.Label(inner, text="Enter ↵", font=FONT_SUB,
                 bg=bg, fg=sfg, anchor="e").place(relx=1.0, x=-14, rely=0.5, anchor="e")
        for w in [outer, inner] + list(inner.winfo_children()):
            w.bind("<Button-1>", lambda e: on_execute())

    all_w = [outer, inner] + list(inner.winfo_children())

    def on_enter(e, o=outer, f=inner):
        if not is_sel and state_val == "ready":
            for w in (o, f): w.config(bg=FILE_CMD_HOV_BG)
            for c in f.winfo_children(): c.config(bg=FILE_CMD_HOV_BG)

    def on_leave(e, o=outer, f=inner):
        if not is_sel:
            for w in (o, f): w.config(bg=FILE_CMD_BG)
            for c in f.winfo_children(): c.config(bg=FILE_CMD_BG)

    for w in all_w:
        w.bind("<Enter>", on_enter)
        w.bind("<Leave>", on_leave)


def _draw_help_rows(parent):
    from fileops import FILE_COMMANDS
    for cmd in FILE_COMMANDS:
        outer = tk.Frame(parent, bg=FILE_CMD_BG, height=ROW_H)
        outer.pack(fill="x")
        outer.pack_propagate(False)
        tk.Frame(outer, bg=FILE_CMD_FG, width=3).pack(side="left", fill="y")
        inner = tk.Frame(outer, bg=FILE_CMD_BG)
        inner.pack(side="left", fill="both", expand=True)
        TEXT_X = 12 + ICON_SIZE + 10
        tk.Label(inner, text=cmd["icon"], font=("Segoe UI", 13),
                 bg=FILE_CMD_BG, fg=FILE_CMD_FG).place(x=10, rely=0.5, anchor="w")
        tk.Label(inner, text=cmd["syntax"], font=FONT_SEL,
                 bg=FILE_CMD_BG, fg=FILE_CMD_FG, anchor="w").place(x=TEXT_X, rely=0.5, anchor="w")
        tk.Label(inner, text=cmd["desc"], font=FONT_SUB,
                 bg=FILE_CMD_BG, fg=FILE_CMD_SUB_FG, anchor="e").place(
                     relx=1.0, x=-14, rely=0.5, anchor="e")
        tk.Frame(outer, bg=DIVIDER_CLR, height=1).place(
            relx=0, rely=1.0, anchor="sw", relwidth=1.0)


def draw_flow_row(parent, idx, flow: dict, is_sel: bool, on_click, on_edit):
    bg   = FLOW_SEL_BG if is_sel else FLOW_BG
    fg   = FLOW_SEL_FG if is_sel else FLOW_FG
    sfg  = FLOW_SUB_FG

    name    = flow.get("name", "Unnamed Flow")
    desc    = flow.get("description", "")
    aliases = flow.get("aliases", [])
    steps   = flow.get("steps", [])
    n_steps = len(steps)

    outer = tk.Frame(parent, bg=bg, height=ROW_H)
    outer.pack(fill="x")
    outer.pack_propagate(False)

    tk.Frame(outer, bg=FLOW_BAR if is_sel else bg, width=3).pack(side="left", fill="y")

    inner = tk.Frame(outer, bg=bg)
    inner.pack(side="left", fill="both", expand=True)

    # right side packed first so it anchors to edge
    preview = desc if desc else "  →  ".join(s.get("value", "") for s in steps[:3])
    if len(preview) > 36:
        preview = preview[:34] + "…"
    tk.Label(inner, text=preview, font=FONT_SUB, bg=bg,
             fg=sfg, anchor="e").pack(side="right", padx=(0, 14))

    ICON_X = 10
    NAME_X = ICON_X + 26

    tk.Label(inner, text=FLOW_ICON, font=("Segoe UI", 13),
             bg=bg, fg=FLOW_BAR).place(x=ICON_X, rely=0.5, anchor="w")

    name_lbl = tk.Label(inner, text=name,
                        font=FONT_SEL if is_sel else FONT_NAME, bg=bg, fg=fg)
    name_lbl.place(x=NAME_X, rely=0.5, anchor="w")

    inner.update_idletasks()
    name_w = name_lbl.winfo_reqwidth()

    badge_text = f"{n_steps} step{'s' if n_steps != 1 else ''}"
    badge_lbl  = tk.Label(inner, text=badge_text, font=("Segoe UI", 7),
                          bg=FLOW_BAR if is_sel else "#2d1f4a",
                          fg="#e9d5ff" if is_sel else FLOW_FG,
                          padx=5, pady=1)
    badge_x = NAME_X + name_w + 8
    badge_lbl.place(x=badge_x, rely=0.5, anchor="w")

    if aliases:
        inner.update_idletasks()
        badge_w   = badge_lbl.winfo_reqwidth()
        alias_str = "  ".join(f">{a}" for a in aliases[:3])
        tk.Label(inner, text=alias_str, font=("Segoe UI", 7),
                 bg="#1a0f2e", fg="#6b3fa0",
                 padx=4, pady=1).place(x=badge_x + badge_w + 5, rely=0.5, anchor="w")

    if not is_sel:
        tk.Frame(outer, bg=DIVIDER_CLR, height=1).place(
            relx=0, rely=1.0, anchor="sw", relwidth=1.0)

    def _widgets():
        return [outer, inner] + list(inner.winfo_children())

    def on_enter(e, o=outer, f=inner, i=idx):
        if i != state.selected:
            for w in (o, f): w.config(bg=FLOW_HOV_BG)
            for c in f.winfo_children():
                if c.cget("bg") not in (FLOW_BAR, "#2d1f4a", "#1a0f2e"):
                    c.config(bg=FLOW_HOV_BG)

    def on_leave(e, o=outer, f=inner, i=idx):
        if i != state.selected:
            for w in (o, f): w.config(bg=FLOW_BG)
            for c in f.winfo_children():
                if c.cget("bg") not in (FLOW_BAR, "#2d1f4a", "#1a0f2e"):
                    c.config(bg=FLOW_BG)

    outer.update_idletasks()
    for w in _widgets():
        w.bind("<Button-1>", lambda e, fl=flow: on_click(fl))
        w.bind("<Enter>",    on_enter)
        w.bind("<Leave>",    on_leave)


def draw_flow_header(parent, on_edit_file):
    hdr = tk.Frame(parent, bg="#0e0c1a", height=28)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)

    tk.Label(hdr, text="⚡  Flows", font=("Segoe UI Semibold", 8),
             bg="#0e0c1a", fg="#6b3fa0").pack(side="left", padx=14)

    edit_lbl = tk.Label(hdr, text="Edit flows.json", font=("Segoe UI", 8),
                        bg="#0e0c1a", fg="#3d2d5a", cursor="hand2")
    edit_lbl.pack(side="right", padx=14)
    edit_lbl.bind("<Button-1>", lambda e: on_edit_file())
    edit_lbl.bind("<Enter>",    lambda e: edit_lbl.config(fg="#a855f7"))
    edit_lbl.bind("<Leave>",    lambda e: edit_lbl.config(fg="#3d2d5a"))

    tk.Frame(parent, bg=DIVIDER_CLR, height=1).pack(fill="x")