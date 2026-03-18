# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

CLI tool (`mtn`) that converts YouTube videos and local audio/video files into structured Markdown notes. Pipeline: URL/file → Groq Whisper transcription → LangChain + Groq LLM → Markdown note with custom template.

## Setup

```bash
poetry install
cp .env.example .env  # add GROQ_API_KEY
```

Requires FFmpeg installed and available in PATH for audio processing.

## CLI Usage

```bash
# YouTube
poetry run mtn youtube "https://youtube.com/watch?v=..."
poetry run mtn youtube "url" --depth avancado
poetry run mtn youtube "url" --depth intermediario --output "path/to/notes/"

# Local audio/video
poetry run mtn local "audio.mp3"
poetry run mtn local "video.mp4" --depth metacognitivo
```

### Depth levels

| Flag | Note style |
|------|-----------|
| `raso` | Quick bullets, max 10 lines |
| `intermediario` | Summary + key points + practical applications (default) |
| `avancado` | Argument analysis, mental frameworks, critical review, connections |
| `metacognitivo` | Deep reflection, personal transformation focus |

## Tests

```bash
poetry run pytest          # all tests
poetry run pytest -v       # verbose
```

## Architecture

```
src/
├── cli.py              # Typer entry point — mtn youtube / mtn local
├── pipeline.py         # Core pipeline logic for both input types
├── services/
│   ├── youtube.py      # yt-dlp metadata + transcript extraction + Whisper fallback
│   └── transcription.py # Groq Whisper API (handles chunking for files > 25MB)
├── core/
│   ├── notes2.py       # LangChain + Groq LLM note generation from template
│   └── audio.py        # Audio chunking (pydub/moviepy — lazy imports for Python 3.13)
└── utils/utils.py      # print_hex_color helper

templates/              # Markdown templates per depth level
tests/                  # Unit tests (pytest)
data/                   # Runtime data — gitignored
  02. audio/
  03. transcriptions/
  04. notes/
```

Key pattern: `pydub` and `moviepy` are imported lazily inside function bodies — do not move them to the top of `audio.py` or `transcription.py` (breaks Python 3.13 due to missing `audioop` module).

## Claude Code Skill

A ready-to-use Claude Code skill lives at `.claude/skills/media-to-notes.md`.

To install it globally:
```bash
# Copy to your Claude Code plugins directory
cp .claude/skills/media-to-notes.md ~/.claude/plugins/local/skills/
```

Once installed, Claude Code can process media directly from any conversation:
> "processa esse vídeo: https://youtu.be/..."
