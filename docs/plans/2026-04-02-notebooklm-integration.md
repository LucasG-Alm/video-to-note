# NotebookLM Integration Plan — Updated

> Atualizad com abordagem baseada em capítulos do YouTube

**Goal:** Integrar NotebookLM-py para resumir capítulos de vídeos longos (> 30 min) ao invés de enviar transcrição bruta ao Groq, reduzindo uso de tokens em ~90%.

**Key Insight:** YouTube videos já têm chapters metadata. Use NotebookLM apenas para **sumarizar por capítulo** com as palavras do apresentador, in lugar de extrair chapters.

**Architecture:** 
- CLI command `mtn config --setup-notebooklm` → Google OAuth → cria 1 notebook reutilizável
- NotebookLMClient wrapper: `.add_youtube_source()` + `.summarize_chapter()` + `.remove_source()`
- YouTube chapters extraídos via yt-dlp, armazenados em JSON
- Pipeline: long video detectado → remove source anterior → add novo video → loop por chapters → pedir resumo de cada um → acumular na nota
- Fallback gracioso: se NotebookLM fail, volta pra Groq pipeline normal

**Tech Stack:** `notebooklm` CLI (via `/notebooklm` skill), `yt-dlp` (chapters), `langchain_groq`, `src/services/transcription.py`, `src/config.py`

**Nota:** Usa CLI `notebooklm` (já instalado via skill) em vez de lib Python diretamente — mais simples, bem testado, com tratamento de erro robusto.

---

## Task 0: Setup NotebookLM OAuth & Create Reusable Notebook

**Files:**
- Create: `src/services/notebooklm_cli.py` — wrapper around CLI `notebooklm`
- Modify: `src/cli.py` — add `config --setup-notebooklm` command
- Modify: `src/config.py` — add `NOTEBOOKLM_*` config keys

**Approach:** Use `notebooklm` CLI (via `/notebooklm` skill) para criar notebook e armazenar ID. Wrapper encapsula chamadas CLI com subprocess.

- [ ] **Step 1: Create CLI wrapper**

File: `src/services/notebooklm_cli.py`

```python
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
```

- [ ] **Step 2: Add CLI command for setup**

File: `src/cli.py` (append to existing `app = typer.Typer()`)

```python
@app.command("config")
def config_command(
    setup_notebooklm: bool = typer.Option(False, "--setup-notebooklm"),
    show: bool = typer.Option(False, "--show"),
):
    """Manage mtn configuration."""
    if show:
        from src.config import get_config
        cfg = get_config()
        print(f"Output dir: {cfg.get('DEFAULT_OUTPUT_DIR')}")
        print(f"NotebookLM: {cfg.get('NOTEBOOKLM_NOTEBOOK_ID', 'Not set')}")
        return
    
    if setup_notebooklm:
        from src.services.notebooklm_cli import setup_oauth_and_create_notebook
        from src.config import save_config_to_env
        
        nb_id, success = setup_oauth_and_create_notebook()
        if success:
            save_config_to_env({"NOTEBOOKLM_NOTEBOOK_ID": nb_id})
            print(f"✅ Setup complete! Notebook: {nb_id}")
        else:
            print(f"❌ Setup failed")
```

- [ ] **Step 3: Update config schema**

File: `src/config.py` (find `VALID_CONFIG_KEYS`)

```python
VALID_CONFIG_KEYS = {
    "DEFAULT_OUTPUT_DIR": str,
    "GROQ_API_KEY": str,
    "NOTEBOOKLM_NOTEBOOK_ID": str,      # NEW
    "NOTEBOOKLM_LAST_SOURCE_ID": str,   # Track for cleanup
}
```

- [ ] **Step 4: Commit**

```bash
git add src/services/notebooklm_cli.py src/cli.py src/config.py
git commit -m "feat: add NotebookLM CLI setup and notebook creation"
```

---

## Task 1: Create NotebookLMClient Wrapper for Chapter Summarization

**Files:**
- Modify: `src/services/notebooklm_cli.py` — add methods for source management and queries
- Create: `tests/unit/test_notebooklm.py`

**Approach:** Extend CLI wrapper with `add_source()`, `remove_source()`, `ask_chapter()` methods.

- [ ] **Step 1: Extend CLI wrapper with source/chat methods**

File: `src/services/notebooklm_cli.py` (append to existing)

```python
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
            return {'source_id': output['source_id'], 'title': output.get('title', 'Video'), 'status': output.get('status', 'processing')}
        return {'source_id': None, 'title': None, 'status': None}
    
    def remove_source(self, source_id: str) -> bool:
        """Remove source from notebook."""
        result = run_notebooklm(f'source delete {source_id} -n {self.notebook_id}', json_output=False)
        return result is not None
    
    def wait_for_source(self, source_id: str, timeout: int = 120) -> bool:
        """Wait for source to be ready."""
        result = run_notebooklm(f'source wait {source_id} -n {self.notebook_id} --timeout {timeout}', json_output=False)
        return result is not None
    
    def summarize_chapter(self, chapter_title: str, start_time: int = 0, end_time: int = 0) -> str:
        """Ask NotebookLM to summarize a chapter."""
        query = f'Faça um breve resumo do capítulo "{chapter_title}" (aprox. {start_time}s a {end_time}s), usando as palavras dos apresentadores, com referências e palavras-chave.'
        
        output = run_notebooklm(
            f'ask "{query}" -n {self.notebook_id} --json',
            json_output=True
        )
        if output and 'answer' in output:
            return output['answer']
        return ""
```

- [ ] **Step 2: Write test for NotebookLMClient**

File: `tests/unit/test_notebooklm.py`

```python
import pytest
from unittest.mock import patch
from src.services.notebooklm_cli import NotebookLMClient

def test_notebooklm_client_init():
    """Client initializes with notebook_id."""
    client = NotebookLMClient("nb-123")
    assert client.notebook_id == "nb-123"

def test_add_youtube_source():
    """add_youtube_source parses CLI output."""
    with patch('src.services.notebooklm_cli.run_notebooklm') as mock_run:
        mock_run.return_value = {'source_id': 'src-abc', 'title': 'Video Title', 'status': 'processing'}
        
        client = NotebookLMClient("nb-123")
        result = client.add_youtube_source("https://youtube.com/watch?v=abc")
        
        assert result['source_id'] == 'src-abc'
        assert result['title'] == 'Video Title'

def test_summarize_chapter():
    """summarize_chapter returns answer from CLI."""
    with patch('src.services.notebooklm_cli.run_notebooklm') as mock_run:
        mock_run.return_value = {'answer': 'Chapter summary text...'}
        
        client = NotebookLMClient("nb-123")
        summary = client.summarize_chapter("Intro", 0, 300)
        
        assert summary == 'Chapter summary text...'

def test_remove_source():
    """remove_source calls CLI delete."""
    with patch('src.services.notebooklm_cli.run_notebooklm') as mock_run:
        mock_run.return_value = "Deleted"
        
        client = NotebookLMClient("nb-123")
        result = client.remove_source("src-abc")
        
        assert result is True
```

Run: `poetry run pytest tests/unit/test_notebooklm.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/services/notebooklm_cli.py tests/unit/test_notebooklm.py
git commit -m "feat: add NotebookLMClient CLI wrapper for chapter summarization"
```

---

## Task 2: Store YouTube Chapters in Transcription JSON

**Files:**
- Modify: `src/services/youtube.py:get_video_metadata()` — extract chapters
- Create: `src/utils/duration_utils.py` — threshold detection
- Create: `tests/unit/test_duration_utils.py`

- [ ] **Step 1: Ensure youtube.py returns chapters**

File: `src/services/youtube.py:get_video_metadata()`

```python
def get_video_metadata(url):
    """Extract metadata including chapters from YouTube."""
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    
    chapters = info.get('chapters', [])
    
    return {
        'title': info.get('title', 'Unknown'),
        'duration_sec': info.get('duration', 0),
        'chapters': [
            {
                'title': ch.get('title', f'Chapter {i+1}'),
                'start_time': ch.get('start_time', 0),
                'end_time': ch.get('end_time', 0),
            }
            for i, ch in enumerate(chapters)
        ],
        # ... rest of metadata ...
    }
```

- [ ] **Step 2: Create duration threshold utility**

File: `src/utils/duration_utils.py`

```python
"""Utilities for detecting video length thresholds."""

LONG_VIDEO_THRESHOLD_SECONDS = 30 * 60  # 30 minutes

def is_long_video(duration_seconds: int | float | None) -> bool:
    """True if duration > 30 min."""
    if not duration_seconds:
        return False
    return duration_seconds > LONG_VIDEO_THRESHOLD_SECONDS
```

File: `tests/unit/test_duration_utils.py`

```python
import pytest
from src.utils.duration_utils import is_long_video

def test_is_long_video_threshold_30_minutes():
    """Videos > 30 minutes marked as long."""
    assert is_long_video(1801) is True   # 30min 1sec
    assert is_long_video(1800) is False  # exactly 30min
    assert is_long_video(900) is False   # 15min
    assert is_long_video(0) is False
    assert is_long_video(None) is False
```

- [ ] **Step 3: Commit**

```bash
git add src/services/youtube.py src/utils/duration_utils.py tests/unit/test_duration_utils.py
git commit -m "feat: extract YouTube chapters and add duration threshold"
```

---

## Task 3: Modify Pipeline to Use NotebookLM for Chapter Summarization

**Files:**
- Modify: `src/pipeline.py:youtube_to_notes()` — add chapter summarization flow
- Create: `tests/integration/test_pipeline_notebooklm.py`

- [ ] **Step 1: Write integration test**

File: `tests/integration/test_pipeline_notebooklm.py`

```python
import pytest
from unittest.mock import patch
from pathlib import Path
from src.pipeline import youtube_to_notes

def test_youtube_to_notes_uses_notebooklm_for_long_video_with_chapters():
    """Long video with chapters uses NotebookLM summarization."""
    with patch('src.pipeline.get_video_metadata') as mock_meta, \
         patch('src.pipeline.NotebookLMClient') as mock_nlm_cls, \
         patch('src.pipeline.is_long_video', return_value=True), \
         patch('src.pipeline.gerar_nota_md') as mock_gerar:
        
        mock_meta.return_value = {
            'title': 'Long Video',
            'duration_sec': 3600,
            'chapters': [
                {'title': 'Intro', 'start_time': 0, 'end_time': 300},
                {'title': 'Main', 'start_time': 300, 'end_time': 3000},
            ]
        }
        
        mock_nlm = mock_nlm_cls.return_value
        mock_nlm.add_youtube_source.return_value = {'source_id': 'src-1', 'title': 'Video', 'status': 'processing'}
        mock_nlm.summarize_chapter.side_effect = ["Summary 1", "Summary 2"]
        mock_nlm.wait_for_source.return_value = True
        
        mock_gerar.return_value = Path('note.md')
        
        result = youtube_to_notes('https://youtube.com/watch?v=abc', depth='intermediario')
        
        assert mock_nlm.add_youtube_source.called
        assert mock_nlm.summarize_chapter.call_count == 2
```

- [ ] **Step 2: Add NotebookLM flow to youtube_to_notes()**

File: `src/pipeline.py` (find `def youtube_to_notes()`)

Add imports:
```python
from src.services.notebooklm_cli import NotebookLMClient
from src.utils.duration_utils import is_long_video
```

Add before Groq fallback logic:
```python
def youtube_to_notes(...):
    """Pipeline: YouTube URL → [NotebookLM if long + chapters] OR [Groq] → note"""
    # ... existing metadata extraction ...
    
    # === NEW: Try NotebookLM for long videos with chapters ===
    if is_long_video(metadata.get('duration_sec', 0)) and metadata.get('chapters'):
        print_hex_color('#32cbff', "📖 Vídeo longo com capítulos — tentando NotebookLM...", "")
        
        try:
            from src.config import get_config, save_config_to_env
            config = get_config()
            nb_id = config.get('NOTEBOOKLM_NOTEBOOK_ID')
            
            if nb_id:
                nlm_client = NotebookLMClient(nb_id)
                
                # Clean up old source
                old_id = config.get('NOTEBOOKLM_LAST_SOURCE_ID')
                if old_id:
                    nlm_client.remove_source(old_id)
                
                # Add video
                src_info = nlm_client.add_youtube_source(url)
                if src_info['source_id']:
                    print_hex_color('#0bd271', f"✅ Vídeo carregado: {src_info['title']}", "")
                    
                    # Wait for source processing
                    nlm_client.wait_for_source(src_info['source_id'])
                    
                    # Summarize chapters
                    summaries = []
                    for i, ch in enumerate(metadata.get('chapters', []), 1):
                        print_hex_color('#32cbff', f"📝 Resumindo {i}/{len(metadata['chapters'])}: {ch['title']}", "")
                        summary = nlm_client.summarize_chapter(
                            ch['title'],
                            ch.get('start_time', 0),
                            ch.get('end_time', 0)
                        )
                        summaries.append({'chapter': ch['title'], 'summary': summary})
                    
                    # Save and generate note
                    metadata['chapter_summaries'] = summaries
                    metadata['transcription_by'] = 'NotebookLM'
                    salvar_transcricao(metadata, {}, str(json_path))
                    save_config_to_env({'NOTEBOOKLM_LAST_SOURCE_ID': src_info['source_id']})
                    
                    try:
                        output = gerar_nota_md(
                            path_transcricao_json=str(json_path),
                            path_template_md=resolve_template(depth),
                            metadata={"tags_md": "YouTube/Vídeo/NotebookLM", "chapter_summaries": summaries},
                            model=model,
                            output_dir=output_dir,
                        )
                        if delay:
                            import random, time
                            wait = random.uniform(90, 150)
                            time.sleep(wait)
                        return output
                    except Exception as e:
                        print_hex_color('#f0a500', f"⚠️  Erro ao gerar nota: {e}", "")
        except Exception as e:
            print_hex_color('#f0a500', f"⚠️  NotebookLM failed: {e}", "")
    
    # === EXISTING: Groq pipeline (unchanged) ===
    # ... rest of existing code ...
```

- [ ] **Step 3: Commit**

```bash
git add src/pipeline.py tests/integration/test_pipeline_notebooklm.py
git commit -m "feat: add NotebookLM chapter summarization with graceful fallback"
```

---

## Task 4: Test E2E with Long YouTube Video

**No code changes — testing only**

- [ ] **Step 1: Run with a real long video**

```bash
cd "C:\Users\lucas\OneDrive\Documentos\_Obsidian\Principal\Projetos\Programação\Media to Notes"
mtn config --setup-notebooklm  # One-time setup
mtn "https://youtu.be/LONG_VIDEO_URL" -d intermediario
```

Expected:
- "📖 Vídeo longo com capítulos — tentando NotebookLM..."
- "✅ Vídeo carregado..."
- "📝 Resumindo cap 1/N..."
- "📝 Resumindo cap 2/N..."
- "✅ Nota salva em _revisar/YouTube/<titulo>.md"

- [ ] **Step 2: Verify note quality**

- Chapters correctly summarized
- Summaries use presenter's words
- Overall length << raw transcript (2-3k tokens vs 10-20k)

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "test: e2e validation with long YouTube video"
```

---

## Task 5: Optional — Add CLI Flag for Force-NotebookLM

**Files:**
- Modify: `src/cli.py` — add `--force-notebooklm` flag

- [ ] **Step 1: Add flag to CLI**

File: `src/cli.py` (find mtn command)

```python
@app.command()
def mtn_command(
    input: str = typer.Argument(...),
    depth: str = typer.Option("intermediario", "-d", "--depth"),
    output: str = typer.Option(None, "-o", "--output"),
    force_notebooklm: bool = typer.Option(False, "--force-notebooklm", help="Use NotebookLM even for short videos"),
):
    """Process YouTube or local media into note."""
    # dispatch to pipeline with flag
```

- [ ] **Step 2: Update pipeline to accept flag**

File: `src/pipeline.py`

```python
def youtube_to_notes(
    url: str,
    ...,
    force_notebooklm: bool = False,  # NEW
):
    # ... in NotebookLM check:
    if (force_notebooklm or is_long_video(...)) and metadata.get('chapters'):
        # ... proceed ...
```

- [ ] **Step 3: Commit**

```bash
git add src/cli.py src/pipeline.py
git commit -m "feat: add --force-notebooklm CLI flag"
```

---

## Summary

**6 tasks:** 0 (OAuth setup) + 1 (NotebookLMClient) + 2 (chapters storage) + 3 (pipeline) + 4 (E2E test) + 5 (optional CLI flag)

**User tested:** ✅ YouTube chapter summarization approach works well

**Next:** Subagent-driven implementation starting with Task 0
