"""NotebookLM CLI wrapper for notebook and source management."""

import subprocess
import json
from src.utils.utils import print_hex_color


def run_notebooklm(command: str, json_output: bool = False) -> dict | str | None:
    """
    Run notebooklm CLI command and return output.

    Args:
        command: Full CLI command string, e.g., "list --json"
        json_output: If True, parse and return JSON; else return stdout

    Returns:
        Parsed JSON dict if json_output=True, else stdout string, or None if failed
    """
    try:
        cmd = f"notebooklm {command}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            print_hex_color('#f0a500', f"⚠️  notebooklm failed: {result.stderr}", "")
            return None

        if json_output:
            return json.loads(result.stdout)
        return result.stdout.strip()
    except Exception as e:
        print_hex_color('#f0a500', f"⚠️  Error running notebooklm: {e}", "")
        return None


def setup_oauth_and_create_notebook() -> tuple[str, bool]:
    """
    Run `notebooklm login` and create reusable notebook.

    Returns:
        (notebook_id, success)
    """
    print("🔐 NotebookLM OAuth Setup")
    print("📖 Opening browser for Google login...")

    # Trigger login
    result = run_notebooklm("login")
    if not result:
        return None, False

    # Verify auth
    status = run_notebooklm("status")
    if not status:
        return None, False

    # Create notebook
    output = run_notebooklm('create "Media to Notes - Processing" --json', json_output=True)
    if not output or 'id' not in output:
        return None, False

    return output['id'], True
