"""
JobTrail setup script.
Registers this MCP server with your chosen AI client by writing
(or safely merging into) that client's config file.
"""

import json
import os
import platform
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_PATH = os.path.join(PROJECT_DIR, "venv", "bin", "python3")
SERVER_PATH = os.path.join(PROJECT_DIR, "server.py")

if platform.system() == "Windows":
    PYTHON_PATH = os.path.join(PROJECT_DIR, "venv", "Scripts", "python.exe")


def get_config_path(client: str) -> str:
    home = os.path.expanduser("~")
    system = platform.system()

    if client == "claude":
        if system == "Windows":
            return os.path.join(os.environ.get("APPDATA", ""), "Claude", "claude_desktop_config.json")
        return os.path.join(home, "Library", "Application Support", "Claude", "claude_desktop_config.json")

    if client == "antigravity":
        return os.path.join(home, ".gemini", "config", "mcp_config.json")

    if client == "cursor":
        return os.path.join(home, ".cursor", "mcp.json")

    if client == "cline":
        if system == "Windows":
            return os.path.join(os.environ.get("APPDATA", ""), "Code", "User", "globalStorage",
                                 "saoudrizwan.claude-dev", "settings", "cline_mcp_settings.json")
        return os.path.join(home, "Library", "Application Support", "Code", "User", "globalStorage",
                             "saoudrizwan.claude-dev", "settings", "cline_mcp_settings.json")

    if client == "vscode":
        # VS Code's native MCP support is project-scoped, not global.
        return os.path.join(PROJECT_DIR, ".vscode", "mcp.json")

    raise ValueError(f"Unknown client: {client}")


def register_server(config_path: str, key: str = "mcpServers"):
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️  {config_path} exists but isn't valid JSON. Please check it manually.")
                sys.exit(1)
    else:
        config = {}

    if key not in config:
        config[key] = {}

    entry = {
        "command": PYTHON_PATH,
        "args": [SERVER_PATH]
    }

    # VS Code's native format additionally wants a "type" field
    if key == "servers":
        entry["type"] = "stdio"

    config[key]["jobtrail"] = entry

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"✅ JobTrail registered in {config_path}")


def main():
    print("JobTrail Setup")
    print("Which AI client do you want to connect JobTrail to?\n")
    print("  1. Claude Desktop")
    print("  2. Antigravity")
    print("  3. Cursor")
    print("  4. Cline (VS Code extension)")
    print("  5. VS Code (native Copilot MCP)")

    choice = input("\nEnter a number (1-5): ").strip()

    client_map = {
        "1": "claude",
        "2": "antigravity",
        "3": "cursor",
        "4": "cline",
        "5": "vscode",
    }

    client = client_map.get(choice)
    if not client:
        print("Invalid choice. Please run again and enter 1-5.")
        sys.exit(1)

    if not os.path.exists(PYTHON_PATH):
        print(f"⚠️  Couldn't find a virtual environment at {PYTHON_PATH}.")
        print("   Run this first:")
        print("     python3 -m venv venv")
        print("     source venv/bin/activate   (or venv\\Scripts\\activate on Windows)")
        print("     pip install -r requirements.txt")
        sys.exit(1)

    config_path = get_config_path(client)
    key = "servers" if client == "vscode" else "mcpServers"
    register_server(config_path, key)

    print("\nNext steps:")
    if client == "vscode":
        print(f"  1. Reload the VS Code window (Cmd/Ctrl+Shift+P → 'Developer: Reload Window').")
    else:
        print(f"  1. Fully quit and reopen your AI client.")
    print(f"  2. Ask it something like: \"List my job applications\"")
    print(f"  3. The first Gmail-related request will open a browser to authorize access.")


if __name__ == "__main__":
    main()