# Media to Notes

> Converte vídeos, áudios e reuniões em notas Markdown estruturadas para o Obsidian.

---

## Visão Geral

| Campo | Detalhe |
|-------|---------|
| **Status** | Em desenvolvimento ativo |
| **Repositório** | [LucasG-Alm/video-to-note](https://github.com/LucasG-Alm/video-to-note) |
| **Stack** | Python 3.13, Poetry, Groq API (Whisper + LLaMA), yt-dlp |
| **Vault** | Obsidian Principal — `Projetos/Programação/Media to Notes/` |

---

## Problema que Resolve

Profissionais consomem grandes volumes de vídeos, áudios e reuniões mas não conseguem transformar isso em conhecimento estruturado. O resultado é:

- Transcrições brutas que nunca são revisadas
- Insights perdidos por falta de organização
- Notas inconsistentes — ora superficiais, ora exageradamente densas
- Tarefas e decisões que ficam enterradas em gravações

---

## Como Funciona

```
INPUT (YouTube URL / arquivo local / áudio)
    ↓
TRANSCRIÇÃO (Groq Whisper API — rápido, quasi-grátis)
    ↓
GERAÇÃO DE NOTA (LLaMA via Groq + template Markdown)
    ↓
OUTPUT (.md pronto para Obsidian)
```

---

## Inputs Suportados

| Tipo | Como |
|------|------|
| YouTube | URL → yt-dlp baixa legenda automática; fallback: baixa áudio + Whisper |
| Arquivo local | MP4, MKV, MP3, WAV, OPUS |
| Áudio de reunião | WhatsApp, Telegram, gravações |

---

## Níveis de Profundidade

| Nível | O que gera |
|-------|------------|
| **Raso** | Bullets rápidos, máximo 10 linhas |
| **Intermediário** | Resumo + termos + aplicações práticas |
| **Avançado** | Frameworks, análise crítica, interconexões |
| **Meta Cognitivo** | Reflexão profunda, impacto pessoal, tensões |

---

## Arquitetura

```
src/
├── cli.py              ← Entry point: mtn youtube / mtn local
├── pipeline.py         ← Orquestra o fluxo para cada tipo de entrada
├── core/
│   ├── notes2.py       ← Geração de nota via LLM + templates
│   └── audio.py        ← Extração e chunking de áudio (lazy imports)
├── services/
│   ├── youtube.py      ← yt-dlp: metadados, legenda, download de áudio
│   └── transcription.py ← Groq Whisper API (direto e chunked)
└── utils/
    └── utils.py        ← print_hex_color (log colorido)

templates/
├── template_youtube_raso.md
├── template_youtube_intermediario.md
├── template_youtube_avancado.md
└── template_youtube_metacognitivo.md

.claude/
└── skills/
    └── media-to-notes.md  ← Skill instalável para o Claude Code

tests/
├── test_youtube_utils.py   ← 15 testes
├── test_notes2_utils.py    ← 13 testes
├── test_pipeline_utils.py  ← 7 testes
└── test_cli.py             ← 12 testes
```

---

## Progresso por Sprint

### ✅ Sprint 1 — Bugs Críticos (concluído)

| # | Fix | Arquivo |
|---|-----|---------|
| 1 | `break` → fallback Whisper ativo | `src/tests/test_youtube.py` |
| 2 | Guards `__main__` — evita execução ao importar | `src/tests/test_youtube.py` |
| 3 | `df[0]` → `iloc[0]` em `arquivo_mais_recente` | `src/core/file_handler.py` |
| 4 | Validação da `GROQ_API_KEY` com `raise ValueError` | `src/core/notes.py` |
| 5 | `print_hex_color` consolidada em `utils.py` | `transcription.py`, `youtube.py` |

### ✅ Sprint 2 — Portabilidade e Qualidade (concluído)

| # | O que foi feito | Impacto |
|---|----------------|---------|
| 1 | `pathlib.Path` em todos os arquivos | Funciona em Windows, macOS e Linux |
| 2 | `notes.py` (legado) deletado | `notes2.py` é o sistema ativo |
| 3 | Dead code removido | Código 30% mais limpo |
| 4 | Path hardcoded `D:\Users\Lucas\...` → `PROJECT_ROOT` relativo | Funciona em qualquer máquina |
| 5 | Imports `pydub`/`moviepy` tornados lazy | Compatibilidade com Python 3.13 |
| 6 | `.gitignore` cobre `data/` + formatos de áudio | Sem vídeos/áudios no git |

### ✅ Sprint 3 — Testes Unitários (concluído)

28 testes, 0 falhas.

| Arquivo de Teste | Funções Cobertas |
|-----------------|-----------------|
| `test_youtube_utils.py` | `extract_video_id` (7), `sanitize_filename` (5), `transcript_to_text` (3) |
| `test_notes2_utils.py` | `gerar_capitulos_formatado` (5), `preencher_variables` (5), `ler_md_template` (3) |

**Bug encontrado pelos testes:** `extract_video_id` não suportava URLs de Shorts — regex corrigida.

### ✅ Sprint 4 — CLI com Typer (concluído)

```bash
poetry run mtn youtube "https://youtu.be/..." --depth avancado
poetry run mtn local "audio.mp3" --depth metacognitivo --output "~/vault/_revisar/"
```

| Arquivo | O que faz |
|---------|-----------|
| `src/cli.py` | Entry point Typer com comandos `youtube` e `local` |
| `src/pipeline.py` | Lógica de negócio para cada tipo de entrada |
| `templates/template_youtube_*.md` | 4 templates por nível de profundidade |

Mais 19 testes adicionados (total: **47 testes, 0 falhas**).

### ✅ Sprint 5 — Claude Code Skill (concluído)

Skill instalável em `.claude/skills/media-to-notes.md`. Permite ao Claude Code processar mídia diretamente de uma conversa:

> *"processa esse vídeo: https://youtu.be/..."*

Instalação:
```bash
cp .claude/skills/media-to-notes.md ~/.claude/plugins/local/skills/
```

---

## Como Rodar

```bash
# Instalar dependências
poetry install

# Rodar testes
poetry run pytest -v

# CLI
poetry run mtn youtube "https://youtu.be/..."
poetry run mtn local "audio.mp3" --depth avancado
```

---

## Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha:

```env
GROQ_API_KEY=gsk_...
```

---

## Roadmap

| Funcionalidade | Status |
|----------------|--------|
| CLI com Typer | ✅ Concluído |
| 4 templates de profundidade | ✅ Concluído |
| Testes unitários (47 testes) | ✅ Concluído |
| Claude Code skill | ✅ Concluído |
| Suporte a Shorts e URLs com timestamp | ✅ Concluído |
| Testes mockados para APIs externas (Groq, yt-dlp) | 🕐 Implementação futura |
| Pesquisa ao estilo Perplexity — busca + síntese + citações | 🔭 Ideia futura |
