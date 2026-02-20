from scanner import build_commands
from ui.window import run_ui
from config import HOTKEY

def main():
    print("[pycast] scanning apps...")
    commands = build_commands()
    print(f"[pycast] {len(commands)} commands loaded")
    print(f"[pycast] ready — press {HOTKEY}")
    try:
        run_ui(commands, HOTKEY)
    except KeyboardInterrupt:
        pass
    print("[pycast] exited")

if __name__ == "__main__":
    main()