# mtn — Media to Notes

> Turn any video or audio into a structured Markdown note. One command.

```bash
poetry run mtn youtube "https://youtube.com/watch?v=..."
# ✅ Nota gerada: data/04. notes/Youtube/Como Pensar Melhor.md
```

Built for [Obsidian](https://obsidian.md). Powered by [Groq](https://console.groq.com/) (Whisper + LLaMA).

---

## What it does

`mtn` takes a YouTube URL or a local audio/video file, transcribes it, and asks an LLM to turn that transcript into a note — with the structure and depth you choose.

```
URL or file
    │
    ▼
yt-dlp (VTT subtitles)          Groq Whisper API
    │   if no subtitles ──────────────────────▶ │
    │◀───────────────────────────────────────────
    │
    ▼
Transcript (with timestamps)
    │
    │  long video? auto-chunked into parts ──▶ summarized ──▶ merged
    │
    ▼
LLaMA 3.3 70B  (rate limit? falls back to LLaMA 3.1 8B)
    │
    ▼
Markdown note  →  your Obsidian vault
```

---

## Features

- **YouTube & local files** — URL, `.mp3`, `.mp4`, `.wav`, `.m4a`, `.mkv`, `.webm`
- **4 depth levels** — from quick bullets to metacognitive reflection
- **Long video support** — auto-chunks transcripts > 8k tokens; tested up to 265 min
- **Smart caching** — skips re-download if transcript already exists on disk
- **Chapter mode** — `--by-chapter` generates one `##` section per video chapter
- **Automatic fallback** — primary model hits rate limit → switches to 8b instantly
- **Customizable templates** — Markdown files with `{{variables}}`
- **102 tests** — pytest, fully mocked, no API calls

---

## Installation

**Requirements:** Python 3.11+, [FFmpeg](https://ffmpeg.org/) in PATH, [Groq API key](https://console.groq.com/)

```bash
git clone https://github.com/LucasG-Alm/video-to-note
cd video-to-note
poetry install
cp .env.example .env   # add GROQ_API_KEY=...
```

---

## Usage

```bash
# YouTube — default depth (intermediario)
poetry run mtn youtube "https://youtube.com/watch?v=..."

# Choose depth and output folder
poetry run mtn youtube "url" --depth avancado --output "~/vault/_revisar/"

# Chapter-based note (one ## section per chapter)
poetry run mtn youtube "url" --by-chapter

# Local file
poetry run mtn local "recording.mp3"
poetry run mtn local "lecture.mp4" --depth metacognitivo --lang en
```

### Depth levels

| Flag | Output style |
|------|-------------|
| `raso` | Quick bullets, max 10 lines |
| `intermediario` | Summary + key points + practical applications *(default)* |
| `avancado` | Central thesis, mental frameworks, critical analysis, connections |
| `metacognitivo` | Deep reflection, tensions, personal transformation |

### All options

```
--depth, -d      raso | intermediario | avancado | metacognitivo
--output, -o     Destination folder for the generated note
--lang, -l       Transcript language: pt (default), en, es, ...
--model          Override the LLM model
--by-chapter     Generate one section per video chapter
```

---

## Output example

```markdown
---
page: "[[YouTube]]"
tags:
  - YouTube/Vídeo
link: https://youtube.com/watch?v=...
autor: "[[Channel Name]]"
data_nota: 2025-08-29
duracao: 1h23m14s
status: inbox
---

## Resumo
...

## Pontos principais
- ...

## Termos e conceitos-chave
**Conceito** — definição em uma linha.

## Aplicações práticas
- ...

## Pulo do gato
...
```

---

## Architecture

```
src/
├── cli.py              # Typer entry point — mtn youtube / mtn local
├── pipeline.py         # Orchestrates the full flow; transcript cache
├── services/
│   ├── youtube.py      # yt-dlp: metadata, VTT subtitles, audio download
│   └── transcription.py # Groq Whisper (chunking for files > 25 MB)
├── core/
│   ├── notes2.py       # LLM note generation; chunking; model fallback
│   └── audio.py        # Audio splitting by silence/size (pydub/moviepy)
└── utils/utils.py      # Colored terminal output

templates/              # One .md template per depth level
tests/                  # 102 unit tests, fully mocked
```

Key design decisions:
- **Lazy imports** for `pydub` and `moviepy` — avoids Python 3.13 `audioop` breakage
- **HumanMessage** instead of `ChatPromptTemplate` — prevents `{variable}` conflicts in code transcripts
- **Two-layer resilience**: chunking handles long transcripts; model fallback handles rate limits

---

## Tests

```bash
poetry run pytest       # all 102 tests
poetry run pytest -v    # verbose
poetry run pytest tests/test_notes2_utils.py  # specific module
```

---

## Roadmap

| Feature | Status |
|---------|--------|
| YouTube + local file pipeline | ✅ |
| 4 depth templates | ✅ |
| Auto-chunking for long videos | ✅ |
| Model fallback on rate limit (TPM) | ✅ |
| VTT timestamps for chapter splitting | ✅ |
| `--by-chapter` flag | ✅ |
| Transcript cache (skip re-download) | ✅ |
| 102 unit tests | ✅ |
| Enricher — link vault notes before LLM call | 🔭 v2 |
| `--editorial` — per-chapter analysis pass | 🔭 v2 |

---

## License

MIT
