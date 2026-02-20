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

# Web search row — slightly distinct tint
WEB_BG     = "#161616"
WEB_HOV_BG = "#1e2030"
WEB_SEL_BG = "#0f2040"
WEB_FG     = "#7aaeee"
WEB_SEL_FG = "#a0c8ff"
WEB_SUB_FG = "#3a3a3a"


def draw_row(parent, idx, name, is_sel, commands, on_click):
    row_bg  = ROW_SEL_BG if is_sel else ROW_BG
    text_fg = ROW_SEL_FG if is_sel else ROW_FG
    sub_fg  = ROW_SEL_SUB if is_sel else ROW_SUB_FG
    font    = FONT_SEL    if is_sel else FONT_NAME

    # ── outer container (fixed height so rows never compress) ────────────
    outer = tk.Frame(parent, bg=row_bg, height=ROW_H)
    outer.pack(fill="x")
    outer.pack_propagate(False)

    # left accent bar
    tk.Frame(outer, bg=ROW_SEL_BAR if is_sel else row_bg, width=3).pack(
        side="left", fill="y"
    )

    inner = tk.Frame(outer, bg=row_bg)
    inner.pack(side="left", fill="both", expand=True)

    # ── icon ─────────────────────────────────────────────────────────────
    photo = get_icon(name, commands)
    if photo:
        lbl = tk.Label(inner, image=photo, bg=row_bg, bd=0)
        lbl.image = photo           # keep reference alive
        lbl.place(x=12, rely=0.5, anchor="w")
    else:
        # fallback: dark square with first letter
        box = tk.Frame(inner, bg=ICON_BG, width=ICON_SIZE, height=ICON_SIZE)
        box.place(x=12, rely=0.5, anchor="w")
        tk.Label(
            box,
            text=name[0].upper(),
            font=("Segoe UI Semibold", 8),
            bg=ICON_BG,
            fg=ICON_FG,
        ).place(relx=0.5, rely=0.5, anchor="center")

    TEXT_X = 12 + ICON_SIZE + 10

    # app name
    tk.Label(inner, text=name, font=font, bg=row_bg, fg=text_fg, anchor="w").place(
        x=TEXT_X, rely=0.5, anchor="w"
    )

    # path hint
    cmd  = commands[name]
    hint = os.path.basename(cmd) if os.path.isabs(cmd) else cmd
    if len(hint) > 38:
        hint = "…" + hint[-36:]
    tk.Label(inner, text=hint, font=FONT_SUB, bg=row_bg, fg=sub_fg, anchor="e").place(
        relx=1.0, x=-14, rely=0.5, anchor="e"
    )

    # row divider (skip on selected row)
    if not is_sel:
        tk.Frame(outer, bg=DIVIDER_CLR, height=1).place(
            relx=0, rely=1.0, anchor="sw", relwidth=1.0
        )

    # ── hover / click ────────────────────────────────────────────────────
    all_widgets = [outer, inner] + list(inner.winfo_children())

    def on_enter(e, o=outer, f=inner, i=idx):
        if i != state.selected:
            for w in (o, f):            w.config(bg=ROW_HOV_BG)
            for c in f.winfo_children(): c.config(bg=ROW_HOV_BG)

    def on_leave(e, o=outer, f=inner, i=idx):
        if i != state.selected:
            for w in (o, f):            w.config(bg=ROW_BG)
            for c in f.winfo_children(): c.config(bg=ROW_BG)

    for w in all_widgets:
        w.bind("<Button-1>", lambda e, n=name: on_click(n))
        w.bind("<Enter>",    on_enter)
        w.bind("<Leave>",    on_leave)


def draw_web_search_row(parent, query: str, is_sel: bool, on_click):
    """
    A special row pinned at the bottom of the list.
    Shows:  🌐  Search Google for "<query>"          Tab
    Clicking or pressing Tab triggers on_click(query).
    """
    bg     = WEB_SEL_BG if is_sel else WEB_BG
    fg     = WEB_SEL_FG if is_sel else WEB_FG
    sub_fg = WEB_SUB_FG

    # top divider to visually separate from app rows
    tk.Frame(parent, bg=DIVIDER_CLR, height=1).pack(fill="x")

    outer = tk.Frame(parent, bg=bg, height=ROW_H)
    outer.pack(fill="x")
    outer.pack_propagate(False)

    # accent bar (blue when selected, invisible otherwise)
    tk.Frame(outer, bg=ROW_SEL_BAR if is_sel else bg, width=3).pack(side="left", fill="y")

    inner = tk.Frame(outer, bg=bg)
    inner.pack(side="left", fill="both", expand=True)

    # globe icon
    tk.Label(
        inner,
        text="🌐",
        font=("Segoe UI", 13),
        bg=bg,
        fg=fg,
    ).place(x=10, rely=0.5, anchor="w")

    TEXT_X = 12 + ICON_SIZE + 10

    # label
    short_q = query if len(query) <= 40 else query[:38] + "…"
    tk.Label(
        inner,
        text=f'Search Google for "{short_q}"',
        font=FONT_NAME,
        bg=bg,
        fg=fg,
        anchor="w",
    ).place(x=TEXT_X, rely=0.5, anchor="w")

    # Tab hint on the right
    tk.Label(
        inner,
        text="Tab",
        font=FONT_SUB,
        bg=bg,
        fg=sub_fg,
        anchor="e",
    ).place(relx=1.0, x=-14, rely=0.5, anchor="e")

    # hover / click
    all_widgets = [outer, inner] + list(inner.winfo_children())

    def on_enter(e, o=outer, f=inner):
        if not is_sel:
            for w in (o, f):             w.config(bg=WEB_HOV_BG)
            for c in f.winfo_children(): c.config(bg=WEB_HOV_BG)

    def on_leave(e, o=outer, f=inner):
        if not is_sel:
            for w in (o, f):             w.config(bg=WEB_BG)
            for c in f.winfo_children(): c.config(bg=WEB_BG)

    for w in all_widgets:
        w.bind("<Button-1>", lambda e: on_click(query))
        w.bind("<Enter>",    on_enter)
        w.bind("<Leave>",    on_leave)


# ─────────────────────────────────────────────
#  FILE COMMAND ROW
# ─────────────────────────────────────────────
FILE_CMD_BG      = "#131820"
FILE_CMD_HOV_BG  = "#1a2030"
FILE_CMD_SEL_BG  = "#0d2137"
FILE_CMD_FG      = "#60a8e0"
FILE_CMD_SEL_FG  = "#90c8ff"
FILE_CMD_SUB_FG  = "#384858"
FILE_CMD_ERR_FG  = "#e05050"
FILE_CMD_OK_FG   = "#50c878"


def draw_file_command_row(parent, parsed: dict, is_sel: bool, on_execute):
    """
    Draws the file command preview row based on the parsed command state.

      help   → show all available commands
      hint   → show syntax for the matched command
      ready  → show what will happen, press Enter to execute
      error  → show what's wrong in red
    """
    state_val = parsed.get("state", "error")

    bg     = FILE_CMD_SEL_BG if is_sel else FILE_CMD_BG
    fg     = FILE_CMD_SEL_FG if is_sel else FILE_CMD_FG
    sub_fg = FILE_CMD_SUB_FG

    # top separator
    tk.Frame(parent, bg=DIVIDER_CLR, height=1).pack(fill="x")

    if state_val == "help":
        _draw_help_rows(parent)
        return

    outer = tk.Frame(parent, bg=bg, height=ROW_H)
    outer.pack(fill="x")
    outer.pack_propagate(False)

    # accent bar
    bar_clr = ROW_SEL_BAR if is_sel else (
        FILE_CMD_ERR_FG if state_val == "error" else FILE_CMD_FG
    )
    tk.Frame(outer, bg=bar_clr, width=3).pack(side="left", fill="y")

    inner = tk.Frame(outer, bg=bg)
    inner.pack(side="left", fill="both", expand=True)

    icon = parsed.get("icon", "📁")
    tk.Label(inner, text=icon, font=("Segoe UI", 13), bg=bg, fg=fg).place(
        x=10, rely=0.5, anchor="w"
    )

    TEXT_X = 12 + ICON_SIZE + 10

    if state_val == "error":
        msg = parsed.get("message", "Error")
        tk.Label(inner, text=msg, font=FONT_NAME, bg=bg,
                 fg=FILE_CMD_ERR_FG, anchor="w").place(x=TEXT_X, rely=0.5, anchor="w")

    elif state_val == "hint":
        syntax = parsed.get("syntax", "")
        desc   = parsed.get("desc", "")
        tk.Label(inner, text=syntax, font=FONT_SEL, bg=bg, fg=fg, anchor="w").place(
            x=TEXT_X, rely=0.5, anchor="w")
        tk.Label(inner, text=desc, font=FONT_SUB, bg=bg, fg=sub_fg, anchor="e").place(
            relx=1.0, x=-14, rely=0.5, anchor="e")

    elif state_val == "ready":
        desc = parsed.get("desc", "")
        tk.Label(inner, text=desc, font=FONT_NAME, bg=bg, fg=fg, anchor="w").place(
            x=TEXT_X, rely=0.5, anchor="w")
        hint_lbl = "Enter ↵" if is_sel else "Enter ↵"
        tk.Label(inner, text=hint_lbl, font=FONT_SUB, bg=bg, fg=sub_fg, anchor="e").place(
            relx=1.0, x=-14, rely=0.5, anchor="e")

        # click or Enter executes
        for w in [outer, inner] + list(inner.winfo_children()):
            w.bind("<Button-1>", lambda e: on_execute())

    # hover
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
    """Show one row per available file command."""
    from fileops import FILE_COMMANDS
    for cmd in FILE_COMMANDS:
        outer = tk.Frame(parent, bg=FILE_CMD_BG, height=ROW_H)
        outer.pack(fill="x")
        outer.pack_propagate(False)
        tk.Frame(outer, bg=FILE_CMD_FG, width=3).pack(side="left", fill="y")
        inner = tk.Frame(outer, bg=FILE_CMD_BG)
        inner.pack(side="left", fill="both", expand=True)
        tk.Label(inner, text=cmd["icon"], font=("Segoe UI", 13),
                 bg=FILE_CMD_BG, fg=FILE_CMD_FG).place(x=10, rely=0.5, anchor="w")
        TEXT_X = 12 + ICON_SIZE + 10
        tk.Label(inner, text=cmd["syntax"], font=FONT_SEL,
                 bg=FILE_CMD_BG, fg=FILE_CMD_FG, anchor="w").place(x=TEXT_X, rely=0.5, anchor="w")
        tk.Label(inner, text=cmd["desc"], font=FONT_SUB,
                 bg=FILE_CMD_BG, fg=FILE_CMD_SUB_FG, anchor="e").place(
            relx=1.0, x=-14, rely=0.5, anchor="e")
        tk.Frame(outer, bg=DIVIDER_CLR, height=1).place(
            relx=0, rely=1.0, anchor="sw", relwidth=1.0)