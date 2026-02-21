import json
import os
import subprocess
import time

FLOWS_FILE = os.path.join(os.path.dirname(__file__), "flows.json")

def load_flows() -> list[dict]:
    if not os.path.exists(FLOWS_FILE):
        _create_default_flows_file()
        return []
    try:
        with open(FLOWS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print("[flows] flows.json must be a JSON array")
            return []
        validated = []
        for flow in data:
            if not isinstance(flow, dict):
                continue
            if "name" not in flow or "steps" not in flow:
                print(f"[flows] skipping flow missing name/steps: {flow}")
                continue
            validated.append(flow)
        print(f"[flows] {len(validated)} flows loaded")
        return validated
    except json.JSONDecodeError as e:
        print(f"[flows] JSON parse error in flows.json: {e}")
        return []


def _create_default_flows_file():
    default = [
        {
            "name": "Run Dev",
            "description": "Opens Chrome and VS Code",
            "steps": [
                {"type": "app", "value": "chrome"},
                {"type": "app", "value": "visual studio code"}
            ]
        }
    ]
    try:
        with open(FLOWS_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        print(f"[flows] created starter flows.json at {FLOWS_FILE}")
    except Exception as e:
        print(f"[flows] could not create flows.json: {e}")


def search_flows(query: str, flows: list[dict]) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return flows

    results = []
    for f in flows:
        name    = f.get("name", "").lower()
        aliases = [a.lower() for a in f.get("aliases", [])]

        if q in name or any(q in a for a in aliases):
            results.append(f)

    return results


def run_flow(flow: dict, commands: dict):
    from launcher_core import launch

    name  = flow.get("name", "unnamed")
    steps = flow.get("steps", [])

    print(f"[flows] running '{name}' ({len(steps)} steps)")

    for i, step in enumerate(steps):
        step_type = step.get("type", "").lower()
        value     = step.get("value", "").strip()

        if not value:
            print(f"[flows]   step {i+1}: empty value, skipping")
            continue

        try:
            if step_type == "app":
                matched = _resolve_app(value, commands)
                if matched:
                    print(f"[flows]   step {i+1}: app → '{matched}'")
                    launch(matched, commands)
                else:
                    print(f"[flows]   step {i+1}: app '{value}' not found, skipping")

            elif step_type == "url":
                url = value if value.startswith("http") else f"https://{value}"
                print(f"[flows]   step {i+1}: url → {url}")
                subprocess.Popen(f"start {url}", shell=True)

            else:
                print(f"[flows]   step {i+1}: unknown type '{step_type}', skipping")

        except Exception as e:
            print(f"[flows]   step {i+1}: error — {e}")
        if i < len(steps) - 1:
            time.sleep(0.4)

    print(f"[flows] '{name}' complete")


def _resolve_app(value: str, commands: dict) -> "str | None":
    v = value.lower()
    if v in commands:
        return v

    for k in commands:
        if k.startswith(v):
            return k
    for k in commands:
        if v in k:
            return k

    return None

def open_flows_file():
    try:
        os.startfile(FLOWS_FILE)
    except Exception:
        subprocess.Popen(["notepad", FLOWS_FILE])