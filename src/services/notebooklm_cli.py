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


class NotebookLMClient:
    """Wrapper for NotebookLM CLI with notebook-specific operations."""

    def __init__(self, notebook_id: str):
        self.notebook_id = notebook_id

    def add_youtube_source(self, url: str) -> dict:
        """Add YouTube video to notebook. Returns {source_id, title, status}."""
        output = run_notebooklm(
            f'source add "{url}" -n {self.notebook_id} --json',
            json_output=True
        )
        if output and 'source_id' in output:
            return {
                'source_id': output['source_id'],
                'title': output.get('title', 'Video'),
                'status': output.get('status', 'processing')
            }
        return {'source_id': None, 'title': None, 'status': None}

    def remove_source(self, source_id: str) -> bool:
        """Remove source from notebook."""
        result = run_notebooklm(
            f'source delete {source_id} -n {self.notebook_id}',
            json_output=False
        )
        return result is not None

    def wait_for_source(self, source_id: str, timeout: int = 120) -> bool:
        """Wait for source to be ready."""
        result = run_notebooklm(
            f'source wait {source_id} -n {self.notebook_id} --timeout {timeout}',
            json_output=False
        )
        return result is not None

    def summarize_chapter(self, chapter_title: str, start_time: int = 0, end_time: int = 0) -> str:
        """Ask NotebookLM to summarize a chapter."""
        query = (
            f'Faça um breve resumo do capítulo "{chapter_title}" '
            f'(aprox. {start_time}s a {end_time}s), usando as palavras dos apresentadores, '
            f'com referências e palavras-chave.'
        )

        output = run_notebooklm(
            f'ask "{query}" -n {self.notebook_id} --json',
            json_output=True
        )
        if output and 'answer' in output:
            return output['answer']
        return ""
