---
name: media-to-notes
description: Convert YouTube videos or local files into Markdown notes using the mtn CLI. Triggers when user pastes a YouTube link or provides a media file path. Asks for confirmation and note depth before processing.
---

# Media to Notes Skill

Convert YouTube videos or local audio/video files into structured Markdown notes using the `mtn` CLI with auto-detection.

## Configuration

Before using, ensure these are set:

```
PROJECT_DIR = C:\Users\lucas\OneDrive\Documentos\_Obsidian\Principal\Projetos\Programação\Media to Notes
DEFAULT_OUTPUT_DIR = C:\Users\lucas\OneDrive\Documentos\_Obsidian\Principal\_revisar\YouTube
```

Configure with: `mtn config --set-output "<path>"`

## Trigger conditions

Activate this skill when:
- User pastes a **YouTube URL** (`youtube.com`, `youtu.be`, `/shorts/`) → **ALWAYS ask before processing**
- User provides a **local file path** (`.mp3`, `.mp4`, `.wav`, `.m4a`, etc.) → **ask if not obvious**
- User says: "processa esse vídeo", "gera nota de", "transforma em nota", "summarize", "transcreve"

## Step-by-step

### 1 — YouTube URL detected

When user pastes a YouTube link, ask:

> "Quer gerar uma nota para este vídeo?"
>
> Se sim, prossiga. Se não, pare.

### 2 — Ask for depth

> "Qual profundidade para a nota?"
> - **raso** — bullets rápidos, máximo 10 linhas
> - **intermediario** — resumo + pontos principais + aplicações *(padrão)*
> - **avancado** — análise de frameworks, crítica, interconexões
> - **metacognitivo** — reflexão profunda, impacto pessoal

Always ask unless the user explicitly specifies a depth. If unsure, default to `intermediario`.

### 3 — Run the CLI (OBRIGATÓRIO)

Use the **new unified CLI command** with auto-dispatch:

```bash
cd C:\Users\lucas\OneDrive\Documentos\_Obsidian\Principal\Projetos\Programação\Media to Notes
poetry run mtn "<url>" --depth <depth>
```

**Examples:**
```bash
poetry run mtn "https://www.youtube.com/watch?v=..." --depth intermediario
poetry run mtn "https://youtu.be/abc123" -d avancado
poetry run mtn "C:\path\to\audio.mp3" --depth raso
```

The CLI auto-detects:
- If input is YouTube URL → runs YouTube pipeline
- If input is file path → runs local file pipeline
- Saves to `DEFAULT_OUTPUT_DIR` (currently: `_revisar/YouTube`)

### 4 — Confirm to user

Report the generated note path. Example:
> ✅ Nota gerada: C:\Users\lucas\OneDrive\Documentos\_Obsidian\Principal\_revisar\YouTube\<titulo>.md

## Available depth templates

| Depth | Style |
|-------|-------|
| `raso` | Quick bullets, ≤ 10 lines |
| `intermediario` | Resumo + pontos principais + aplicações práticas |
| `avancado` | Análise de frameworks, crítica, interconexões |
| `metacognitivo` | Reflexão profunda, impacto pessoal |

## Key points

✅ **Always** use the unified `mtn "<input>" --depth <depth>` syntax
✅ **Always** ask user before processing YouTube links
✅ **Always** ask for depth (unless specified)
✅ **Never** use old syntax (`mtn youtube` or `mtn local`)
✅ Auto-detection handles YouTube URLs and local files automatically

## Requirements

- `GROQ_API_KEY` in `.env`
- FFmpeg installed and in PATH
- `poetry install` run at least once
- `DEFAULT_OUTPUT_DIR` configured to `_revisar/YouTube`

## Notes

- Default output: `C:\Users\lucas\OneDrive\Documentos\_Obsidian\Principal\_revisar\YouTube\<title>.md`
- YouTube transcripts use captions first; falls back to Groq Whisper
- Audio files > 25 MB auto-chunked before transcription
- CLI version: v0.2.0+ (with auto-dispatch)
