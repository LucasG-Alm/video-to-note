# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

CLI tool (`mtn`) that converts YouTube videos and local audio/video files into structured Markdown notes. Pipeline: URL/file → Groq Whisper transcription → LangChain + Groq LLM → Markdown note with custom template.

## Setup

```bash
poetry install  # venv em AppData\Local\pypoetry\Cache\virtualenvs\ (fora do OneDrive)
pip install -e .  # instala mtn CLI globalmente
cp .env.example .env  # add GROQ_API_KEY
```

Requires FFmpeg installed and available in PATH for audio processing.

After `pip install -e .`, `mtn` is available globally in the terminal.

### Configuration

**Default output directory:** Notes são salvas em `data/04. notes/` por padrão. Para customizar:

```bash
# Definir diretório de saída padrão
mtn config --set-output "C:/caminho/para/notas"

# Verificar configuração atual
mtn config --show
```

O valor é salvo automaticamente em `.env` como `DEFAULT_OUTPUT_DIR`.

## CLI Usage

### Novo padrão (recomendado)

O CLI detecta automaticamente se a entrada é URL do YouTube ou arquivo local:

```bash
# YouTube (auto-detected)
mtn "https://youtube.com/watch?v=..."
mtn "https://youtube.com/watch?v=..." -d avancado
mtn "https://youtu.be/abc123" --depth intermediario --output "path/to/notes/"

# Local audio/video (auto-detected)
mtn "audio.mp3"
mtn "video.mp4" -d metacognitivo
mtn "C:/Videos/aula.mp4" -d avancado --output "/path/to/notes/"
```

### Gerenciar configuração

```bash
# Ver configuração atual
mtn config --show

# Definir diretório de saída padrão
mtn config --set-output "C:/Users/lucas/notes/"
```

### Compatibilidade — subcomandos antigos (ainda funcionam)

```bash
# YouTube
mtn youtube "url" [--depth raso|intermediario|avancado|metacognitivo] [--output "path"]
mtn youtube "url" --lang pt --model groq-model

# Local
mtn local "path" [--depth ...] [--output ...]
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
├── cli.py              # Typer entry point — mtn <input> / mtn youtube / mtn local
│                       # Auto-dispatch: detecta tipo de input e roteia para comando correto
├── config.py           # Config loader (config.toml) + save_config_to_env()
├── pipeline.py         # Core pipeline logic for both input types
├── services/
│   ├── youtube.py      # yt-dlp metadata + transcript extraction + Whisper fallback
│   └── transcription.py # Groq Whisper API (handles chunking for files > 25MB)
├── core/
│   ├── notes2.py       # LangChain + Groq LLM note generation from template
│   └── audio.py        # Audio chunking (pydub/moviepy — lazy imports for Python 3.13)
└── utils/
    ├── input_detector.py # Detecta tipo de input (YouTube URL vs arquivo local)
    │                      # Valida entrada com mensagens de erro claras
    └── utils.py          # print_hex_color helper

templates/              # Markdown templates per depth level
tests/                  # Unit tests (pytest)
  └── unit/
      ├── test_cli.py              # CLI command tests
      └── test_input_detector.py   # Input detection & validation tests
data/                   # Runtime data — gitignored
  02. audio/
  03. transcriptions/
  04. notes/
```

Key pattern: `pydub` and `moviepy` are imported lazily inside function bodies — do not move them to the top of `audio.py` or `transcription.py` (breaks Python 3.13 due to missing `audioop` module).

**New in v0.2.0:** Auto-dispatch CLI, `mtn config` command, input auto-detection module (`input_detector.py`).

## Roadmap

### v1 (atual) — pipeline base
Foco: fazer o pipeline funcionar de ponta a ponta, sem bugs, no Windows.
Prioridades: corrigir ERR-01 (encoding) e ERR-02 (chunking) antes de qualquer feature nova.

### v2 (ideia registrada — não implementar antes de estabilizar v1)
Adicionar camada de **Enricher** como **comando personalizado do Obsidian** — separado do pipeline.

O pipeline continua gerando a nota base (`mtn youtube ...`). O enriquecimento acontece depois, dentro do Obsidian, sob demanda:
- Escopo configurável: texto selecionado, bloco H2/H3, ou nota inteira
- Fontes plugáveis: Perplexity API (contexto web), notebooklm-py (corpus fechado), ou offline (só classificação)
- Classificação automática de links da descrição antes de enriquecer
- Filtro anti-ruído: só enriquece se cumprir critério de clareza (não de volume)

Arquitetura alvo:
```
mtn pipeline → nota base no vault
                    ↓ (sob demanda, no Obsidian)
              Enricher command → classifica → consulta fonte → injeta na nota
```

Spec completa: `docs/Ideia - Enricher como Comando Obsidian.md`

## Known Issues & Pending Improvements

Documento completo: `docs/Teste - Sessão 2026-03-20.md`

### Bugs críticos (Alta urgência)

**ERR-01 — UnicodeEncodeError no Windows**
- `print_hex_color` usa emojis que quebram com encoding `cp1252` do terminal Windows
- Workaround: `PYTHONIOENCODING=utf-8` antes de rodar qualquer comando
- Fix: adicionar `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` no início de `cli.py`

**ERR-02 — Groq TPM limit em vídeos longos (> ~45min)**
- `llama-3.3-70b-versatile` free tier: limite de 12k tokens. Vídeos longos excedem isso.
- Fix necessário em `notes2.py`: estimar tokens antes de enviar; se exceder, dividir por capítulos ou por blocos de palavras; processar por partes e concatenar.

### Bugs médios

**ERR-03 — `load_dotenv()` falha via stdin/heredoc**
- `find_dotenv()` sem args lança `AssertionError` fora do contexto de arquivo real
- Fix: `load_dotenv(Path(__file__).parent.parent / '.env')` em `notes2.py`

**ERR-04 — Segments da transcrição sem timestamps (start: 0.0)**
- yt-dlp retorna segments com timestamps zerados para legendas automáticas do YouTube
- Impede divisão precisa por capítulos — workaround atual: divisão proporcional por caracteres
- Fix: investigar `--write-subs --sub-format vtt` para preservar timestamps reais

### Melhorias de feature (backlog)

| ID | Descrição | Urgência | Impacto |
|----|-----------|----------|---------|
| M-05 | Flag `--by-chapter` na CLI: processa e agrupa por capítulos automaticamente | 🟡 Média | Alto |
| M-09 | Estimar tokens antes de chamar o LLM, exibir aviso se próximo do limite | 🟡 Média | Médio |
| M-10 | Fallback automático de modelo quando TPM excedido (70b → 8b instant) | 🟡 Média | Alto |
| M-06 | Análise editorial como etapa opcional (`--editorial`) antes de gerar nota | 🟢 Baixa | Alto |
| M-07 | Enriquecimento via vault Obsidian: buscar notas relacionadas antes do LLM | 🟢 Baixa | Alto |
| M-08 | Atualizar yt-dlp: `poetry run pip install -U yt-dlp` (nsig warnings) | 🟢 Baixa | Baixo |

## Claude Code Skill

A ready-to-use Claude Code skill lives at `.claude/skills/media-to-notes.md`.

To install it globally:
```bash
# Copy to your Claude Code plugins directory
cp .claude/skills/media-to-notes.md ~/.claude/plugins/local/skills/
```

Once installed, Claude Code can process media directly from any conversation:
> "processa esse vídeo: https://youtu.be/..."
