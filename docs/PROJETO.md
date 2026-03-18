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

## Níveis de Profundidade (a implementar no CLI)

| Nível | O que gera |
|-------|------------|
| **Raso** | Bullets rápidos, definições básicas |
| **Intermediário** | Resumo + termos + aplicações |
| **Avançado** | Frameworks, análises críticas, interconexões |
| **Meta Cognitivo** | Reflexões sobre propósito, conexões pessoais |

---

## Arquitetura

```
src/
├── core/
│   ├── notes2.py       ← Geração de nota via LLM + templates
│   ├── audio.py        ← Extração e chunking de áudio
│   ├── converter.py    ← Conversão de formatos
│   └── file_handler.py ← Utilitários de arquivo
├── services/
│   ├── youtube.py      ← Download, metadados, transcrição via yt-dlp
│   └── transcription.py ← Groq Whisper API (direto e chunked)
├── utils/
│   └── utils.py        ← print_hex_color (log colorido)
└── interfaces/
    └── app_youtube.py  ← Interface Streamlit (legado)

templates/
├── template_youtube.md ← Template para vídeos do YouTube
└── template_curso.md   ← Template para cursos/aulas

tests/
├── test_youtube_utils.py   ← 15 testes unitários
└── test_notes2_utils.py    ← 13 testes unitários
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

28 testes, 0 falhas, 0.75s de execução.

| Arquivo de Teste | Funções Cobertas |
|-----------------|-----------------|
| `test_youtube_utils.py` | `extract_video_id` (7 casos), `sanitize_filename` (5 casos), `transcript_to_text` (3 casos) |
| `test_notes2_utils.py` | `gerar_capitulos_formatado` (5 casos), `preencher_variables` (5 casos), `ler_md_template` (3 casos) |

**Bug encontrado pelos testes:** `extract_video_id` não suportava URLs de Shorts (`/shorts/XXXXXXXXXXX`) — regex corrigida.

```bash
# Como rodar
poetry run pytest -v
```

### 🔄 Sprint 4 — CLI (em andamento)

Adicionar interface de linha de comando para que a skill Claude Code possa chamar o projeto como engine.

### ⏳ Sprint 5 — Skill Claude Code

Criar `obsidian:media-to-notes` — skill que usa o CLI como engine e cuida da orquestração inteligente (escolha de template, pasta de destino, frontmatter, wikilinks).

---

## Como Rodar

```bash
# Instalar dependências
poetry install

# Rodar testes
poetry run pytest -v

# Streamlit (interface legada)
poetry run streamlit run src/interfaces/app_youtube.py
```

---

## Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha:

```env
GROQ_API_KEY=gsk_...
```

---

## Roadmap

- [ ] Sprint 4: CLI com argparse/typer
- [ ] Sprint 5: Skill `obsidian:media-to-notes`
- [ ] Integração direta com vault Obsidian (output em `_revisar/`)
- [ ] Suporte a WhatsApp/Telegram (já existe parcialmente)
- [ ] Níveis de profundidade no output (Raso → Meta Cognitivo)
- [ ] Testes de integração com mock da Groq API
