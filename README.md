# 🎥 Media to Notes

Converta vídeos do YouTube e arquivos locais de áudio/vídeo em notas Markdown estruturadas para o Obsidian.

Pipeline: **URL ou arquivo → transcrição (Groq Whisper) → nota (LLM)** com templates por profundidade.

> ⚠️ **Uso Pessoal & Educacional:**
> Este projeto não distribui nem incentiva a reprodução de conteúdos protegidos por direitos autorais. Seu objetivo é servir como ferramenta pessoal de organização de conhecimento a partir de conteúdos de uso próprio ou de acesso livre.

---

## Funcionalidades

- 🌐 **YouTube** — extrai legenda automática via yt-dlp; cai no Whisper se não houver
- 🎵 **Arquivos locais** — `.mp3`, `.mp4`, `.wav`, `.m4a`, `.mkv`, `.webm` e outros
- ✂️ **Chunking automático** — arquivos > 25 MB são cortados antes de transcrever
- 📝 **4 níveis de profundidade** — de bullets rápidos até análise crítica ou reflexão metacognitiva
- 🎨 **Templates customizáveis** — Markdown com variáveis preenchidas automaticamente
- 🤖 **Claude Code skill** — processa mídia direto de uma conversa com o Claude

---

## Instalação

```bash
git clone https://github.com/LucasG-Alm/video-to-note
cd video-to-note
poetry install
cp .env.example .env  # adicione sua GROQ_API_KEY
```

**Requisitos:** Python 3.11+, [FFmpeg](https://ffmpeg.org/) no PATH, chave de API da [Groq](https://console.groq.com/).

---

## Uso

```bash
# Vídeo do YouTube
poetry run mtn youtube "https://youtube.com/watch?v=..."

# Com profundidade e pasta de saída customizadas
poetry run mtn youtube "url" --depth avancado --output "~/vault/_revisar/"

# Arquivo local
poetry run mtn local "audio.mp3"
poetry run mtn local "video.mp4" --depth metacognitivo
```

### Níveis de profundidade (`--depth`)

| Nível | Estilo da nota |
|-------|---------------|
| `raso` | Bullets rápidos, máximo 10 linhas |
| `intermediario` | Resumo + pontos principais + aplicações práticas *(padrão)* |
| `avancado` | Tese central, frameworks, análise crítica, interconexões |
| `metacognitivo` | Reflexão profunda, tensões, impacto pessoal |

---

## Arquitetura

```
src/
├── cli.py              # Entry point — mtn youtube / mtn local
├── pipeline.py         # Orquestra o fluxo para cada tipo de entrada
├── services/
│   ├── youtube.py      # yt-dlp: metadados, legenda, download de áudio
│   └── transcription.py # Groq Whisper API (com chunking para arquivos grandes)
├── core/
│   ├── notes2.py       # Geração de nota via LangChain + Groq LLM
│   └── audio.py        # Corte de áudio por silêncio/tamanho (pydub/moviepy)
└── utils/utils.py

templates/              # Templates Markdown por nível de profundidade
tests/                  # Testes unitários (pytest)
data/                   # Runtime — gitignored
  02. audio/
  03. transcriptions/
  04. notes/
```

---

## Claude Code Skill

Este repositório inclui uma skill para o [Claude Code](https://claude.ai/code) em `.claude/skills/media-to-notes.md`.

Com ela instalada, basta dizer ao Claude:
> *"processa esse vídeo: https://youtu.be/..."*

e ele detecta a URL, pergunta o nível de profundidade e executa o pipeline automaticamente.

**Instalação da skill:**
```bash
cp .claude/skills/media-to-notes.md ~/.claude/plugins/local/skills/
```

---

## Testes

```bash
poetry run pytest       # roda todos os testes
poetry run pytest -v    # verbose
```

---

## Roadmap

| Funcionalidade | Status |
|----------------|--------|
| CLI com Typer | ✅ Concluído |
| 4 templates de profundidade | ✅ Concluído |
| Testes unitários (pytest) | ✅ Concluído |
| Claude Code skill | ✅ Concluído |
| Suporte a Shorts e URLs com timestamp | ✅ Concluído |
| Armazenamento MongoDB | 🕐 Planejado |
| Plugin nativo para Obsidian | 🔭 Visão futura |

---

## Licença

MIT — use, adapte, compartilhe. 😎
