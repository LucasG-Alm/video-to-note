<div align="center">

# 🎬 mtn — Media to Notes

### Transforme qualquer vídeo ou áudio em uma nota Markdown estruturada. Um comando.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://console.groq.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-102%20passing-22c55e?style=for-the-badge&logo=pytest&logoColor=white)](tests/)
[![Obsidian](https://img.shields.io/badge/Obsidian-compatible-7C3AED?style=for-the-badge&logo=obsidian&logoColor=white)](https://obsidian.md)

<!-- DEMO GIF: grave o terminal rodando `mtn youtube <url>` até aparecer "✅ Nota gerada" -->
<!-- sugestão de ferramenta: ScreenToGif (Windows) ou Kap (Mac) -->
![Demo](assets/demo.gif)

</div>

---

## ✨ O que faz

**`mtn`** recebe uma URL do YouTube ou um arquivo local, transcreve, e pede a um LLM que transforme a transcrição em nota — com a estrutura e profundidade que você escolher.

```bash
poetry run mtn youtube "https://youtube.com/watch?v=..."
# ✅ Nota gerada: data/04. notes/Youtube/Como Pensar Melhor.md
```

---

## 🔄 Pipeline

```
📎 URL ou arquivo
        │
        ▼
   yt-dlp (legendas VTT)      🎙️ Groq Whisper API
        │  sem legenda? ──────────────────────▶ │
        │◀───────────────────────────────────────
        │
        ▼
📄 Transcrição (com timestamps)
        │
        │  vídeo longo? divide em partes ──▶ resume cada uma ──▶ junta
        │
        ▼
🤖 LLaMA 3.3 70B  (rate limit? cai para LLaMA 3.1 8B automaticamente)
        │
        ▼
📝 Nota Markdown  →  📁 seu vault no Obsidian
```

---

## 🚀 Funcionalidades

| | Funcionalidade | Detalhe |
|--|---|---|
| 🌐 | **YouTube & arquivos locais** | URL, `.mp3`, `.mp4`, `.wav`, `.m4a`, `.mkv`, `.webm` |
| 🧠 | **4 níveis de profundidade** | De bullets rápidos até reflexão metacognitiva |
| ✂️ | **Vídeos longos** | Chunking automático > 8k tokens — testado com vídeos de 265 min |
| ♻️ | **Cache de transcrição** | Pula o download se o JSON já existe no disco |
| 📚 | **Modo por capítulos** | `--by-chapter` gera uma seção `##` por capítulo do vídeo |
| ⚡ | **Fallback automático** | Modelo primário no limite? Troca para o 8b instantaneamente |
| 🎨 | **Templates customizáveis** | Arquivos `.md` com `{{variáveis}}` |
| 🧪 | **102 testes** | pytest, totalmente mockado, sem chamadas reais à API |

---

## ⚙️ Instalação

> **Requisitos:** Python 3.11+, [FFmpeg](https://ffmpeg.org/) no PATH, [Groq API key](https://console.groq.com/)

```bash
git clone https://github.com/LucasG-Alm/video-to-note
cd video-to-note
poetry install
cp .env.example .env   # adicione: GROQ_API_KEY=gsk_...
```

---

## 🎮 Uso

```bash
# YouTube — profundidade padrão
poetry run mtn youtube "https://youtube.com/watch?v=..."

# Profundidade e pasta de saída customizadas
poetry run mtn youtube "url" --depth avancado --output "~/vault/_revisar/"

# Nota por capítulos
poetry run mtn youtube "url" --by-chapter

# Arquivo local
poetry run mtn local "gravacao.mp3"
poetry run mtn local "aula.mp4" --depth metacognitivo --lang en
```

### 🎯 Níveis de profundidade (`--depth`)

<!-- IMAGEM: print das 4 notas lado a lado, mostrando diferença visual entre os depths -->
<!-- ex: assets/depth-comparison.png -->

| Nível | Estilo da nota |
|-------|---------------|
| `raso` | Bullets rápidos, máx. 10 linhas |
| `intermediario` | Resumo + pontos principais + aplicações práticas *(padrão)* |
| `avancado` | Tese central, frameworks mentais, análise crítica, interconexões |
| `metacognitivo` | Reflexão profunda, tensões, impacto pessoal |

---

## 📄 Exemplo de nota gerada

<!-- IMAGEM: print da nota aberta no Obsidian com o tema dark -->
<!-- ex: assets/note-example.png -->

```markdown
---
page: "[[YouTube]]"
tags:
  - YouTube/Vídeo
link: https://youtube.com/watch?v=...
autor: "[[Canal]]"
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

## 🏗️ Arquitetura

```
src/
├── cli.py              # Entry point — mtn youtube / mtn local
├── pipeline.py         # Orquestra o fluxo; cache de transcrição
├── services/
│   ├── youtube.py      # yt-dlp: metadados, VTT, download de áudio
│   └── transcription.py # Groq Whisper (chunking para arquivos > 25 MB)
├── core/
│   ├── notes2.py       # Geração via LLM; chunking; fallback de modelo
│   └── audio.py        # Corte de áudio por silêncio/tamanho
└── utils/utils.py      # Output colorido no terminal

templates/              # Um .md por nível de profundidade
tests/                  # 102 testes unitários, totalmente mockados
```

> 💡 **Decisões de design:**
> - `pydub` e `moviepy` importados com **lazy import** — evita quebra no Python 3.13 (`audioop` removido)
> - **`HumanMessage`** direto em vez de `ChatPromptTemplate` — evita conflito com `{variáveis}` em transcrições de código
> - **Resiliência em duas camadas:** chunking resolve transcrições longas; fallback de modelo resolve rate limit

---

## 🧪 Testes

```bash
poetry run pytest               # todos os 102 testes
poetry run pytest -v            # verbose
poetry run pytest tests/test_notes2_utils.py   # módulo específico
```

---

## 🗺️ Roadmap

| Funcionalidade | Status |
|----------------|--------|
| Pipeline YouTube + arquivos locais | ✅ |
| 4 templates de profundidade | ✅ |
| Chunking automático para vídeos longos | ✅ |
| Fallback de modelo em rate limit | ✅ |
| VTT com timestamps para split por capítulo | ✅ |
| Flag `--by-chapter` | ✅ |
| Cache de transcrição (evita re-download) | ✅ |
| 102 testes unitários | ✅ |
| Enricher — busca notas relacionadas no vault antes do LLM | 🔭 v2 |
| `--editorial` — passagem analítica antes de gerar a nota | 🔭 v2 |

---

<div align="center">

MIT License · Feito com ☕ e muita transcrição

</div>
