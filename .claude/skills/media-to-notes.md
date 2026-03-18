---
name: media-to-notes
description: Process a YouTube URL or local audio/video file into a structured Markdown note. Triggers when the user pastes a YouTube link, provides a media file path, or asks to generate a note from a video/audio source.
---

# Media to Notes Skill

Convert YouTube videos or local audio/video files into structured Markdown notes using the `mtn` CLI.

## Configuration

Before using, set these variables to match your environment:

```
PROJECT_DIR = /path/to/video-to-note   # root of the cloned repo
VAULT_INBOX  = /path/to/obsidian/_revisar/  # where notes land in your vault (optional)
```

## Trigger conditions

Activate this skill when the user:
- Pastes a YouTube URL (contains `youtube.com`, `youtu.be`, or `/shorts/`)
- Provides a path to an audio or video file and wants a note
- Says: "processa esse vídeo", "gera nota de", "transforma em nota", "note this video", "summarize this"

## Step-by-step

### 1 — Identify input type

- URL containing `youtube.com`, `youtu.be`, `shorts/` → **YouTube mode**
- File path ending in `.mp3`, `.mp4`, `.wav`, `.m4a`, `.opus`, `.mkv`, `.webm`, etc. → **Local mode**

### 2 — Select depth

If the user didn't specify a depth, ask:

> "Qual profundidade para a nota?"
> - **raso** — bullets rápidos, máximo 10 linhas
> - **intermediario** — resumo + pontos principais + aplicações práticas *(padrão)*
> - **avancado** — análise de frameworks, crítica, interconexões
> - **metacognitivo** — reflexão profunda, impacto pessoal

If the user seems in a hurry or the content is short, default to `intermediario` without asking.

### 3 — Run the CLI

From `PROJECT_DIR`, run the appropriate command:

**YouTube:**
```bash
cd <PROJECT_DIR>
poetry run mtn youtube "<url>" --depth <depth>
# To output directly to Obsidian vault inbox:
poetry run mtn youtube "<url>" --depth <depth> --output "<VAULT_INBOX>"
```

**Local file:**
```bash
cd <PROJECT_DIR>
poetry run mtn local "<file_path>" --depth <depth>
# With vault output:
poetry run mtn local "<file_path>" --depth <depth> --output "<VAULT_INBOX>"
```

### 4 — Confirm

Report the generated note path to the user. If `--output` pointed to the Obsidian vault, mention the note is ready in the inbox.

## Available depth templates

| Depth | File | Style |
|-------|------|-------|
| `raso` | `template_youtube_raso.md` | Quick bullets, ≤ 10 lines |
| `intermediario` | `template_youtube_intermediario.md` | Resumo + pontos + aplicações |
| `avancado` | `template_youtube_avancado.md` | Tese + frameworks + análise crítica |
| `metacognitivo` | `template_youtube_metacognitivo.md` | Reflexão + tensão + impacto pessoal |

## Requirements

- `GROQ_API_KEY` in `.env` at `PROJECT_DIR`
- FFmpeg installed and in PATH
- `poetry install` run at least once

## Notes

- Default note output (no `--output`): `data/04. notes/Youtube/<title>.md`
- The pipeline tries to get YouTube captions first; falls back to Groq Whisper if none available
- Audio files > 25 MB are automatically chunked before transcription
