from scanner import build_commands
from ui.window import run_ui
from config import HOTKEY

def main():
    print("[launcher] scanning apps...")
    commands = build_commands()
    print(f"[launcher] {len(commands)} commands loaded")
    print(f"[launcher] ready — press {HOTKEY}")
    try:
        run_ui(commands, HOTKEY)
    except KeyboardInterrupt:
        pass
    print("[launcher] exited")

if __name__ == "__main__":
    main()