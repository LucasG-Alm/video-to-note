<p align="center">
  <!-- ÍCONE: crie um ícone 128×128px (sugestão: microfone + folha Markdown) e salve em assets/icon.png -->
  <img src="assets/icon.png" alt="mtn icon" width="128" />
</p>

<h1 align="center">mtn — Media to Notes</h1>

<p align="center">
  Transcreve qualquer vídeo ou áudio e entrega uma nota Markdown estruturada.<br/>
  Um comando. Direto para o seu vault no Obsidian.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Groq-LLaMA%203.3-F55036?style=flat-square" />
  <img src="https://img.shields.io/badge/testes-102%20✓-22c55e?style=flat-square" />
  <img src="https://img.shields.io/badge/licença-MIT-6b7280?style=flat-square" />
</p>

<br/>

<!-- GIF DEMO: grave o terminal rodando `mtn youtube <url>` até aparecer "✅ Nota gerada" (~30s) -->
<!-- ferramenta sugerida: ScreenToGif (Windows) — salve em assets/demo.gif -->
<p align="center">
  <img src="assets/demo.gif" alt="mtn demo" width="720" />
</p>

---

## O que faz

`mtn` recebe uma URL do YouTube ou um arquivo de áudio/vídeo local, transcreve usando a API Whisper da Groq, e pede a um LLM que transforme essa transcrição em nota estruturada — com o nível de profundidade que você definir.

```bash
poetry run mtn youtube "https://youtube.com/watch?v=..."
# ✅ Nota gerada: data/04. notes/Youtube/Como Pensar Melhor.md
```

<!-- SCREENSHOT: print de uma nota aberta no Obsidian (tema dark) mostrando o frontmatter + corpo -->
<!-- salve em assets/note-preview.png -->
<p align="center">
  <img src="assets/note-preview.png" alt="Nota gerada no Obsidian" width="720" />
</p>

---

## Funcionalidades

- 🌐 **YouTube e arquivos locais** — URL, `.mp3`, `.mp4`, `.wav`, `.m4a`, `.mkv`, `.webm` e outros
- 🧠 **4 níveis de profundidade** — de bullets rápidos até reflexão metacognitiva
- ✂️ **Suporte a vídeos longos** — chunking automático acima de 8k tokens; testado com vídeos de até 265 min
- ♻️ **Cache de transcrição** — reutiliza JSON existente no disco, sem re-download
- 📚 **Modo por capítulos** — `--by-chapter` gera uma seção `##` por capítulo do vídeo
- ⚡ **Fallback automático** — modelo primário no limite de rate? troca para o 8b instantaneamente
- 🎨 **Templates customizáveis** — arquivos `.md` com `{{variáveis}}` substituídas automaticamente
- 🧪 **102 testes unitários** — pytest, totalmente mockado, sem chamadas reais à API

---

## Instalação

**Requisitos:** Python 3.11+, [FFmpeg](https://ffmpeg.org/) no PATH, [chave de API Groq](https://console.groq.com/)

```bash
git clone https://github.com/LucasG-Alm/video-to-note
cd video-to-note
poetry install
cp .env.example .env   # adicione: GROQ_API_KEY=gsk_...
```

---

## Uso

```bash
# YouTube
poetry run mtn youtube "https://youtube.com/watch?v=..."

# Com profundidade e pasta de saída customizadas
poetry run mtn youtube "url" --depth avancado --output "~/vault/_revisar/"

# Nota dividida por capítulos do vídeo
poetry run mtn youtube "url" --by-chapter

# Arquivo local
poetry run mtn local "gravacao.mp3"
poetry run mtn local "aula.mp4" --depth metacognitivo --lang en
```

### Níveis de profundidade (`--depth`)

<!-- IMAGEM: os 4 cards lado a lado mostrando diferença visual entre os depths, fundo escuro -->
<!-- salve em assets/depths.png -->
<p align="center">
  <img src="assets/depths.png" alt="Comparação de profundidades" width="720" />
</p>

| Nível | Estilo da nota |
|-------|----------------|
| `raso` | Bullets rápidos, máx. 10 linhas |
| `intermediario` | Resumo + pontos principais + aplicações práticas *(padrão)* |
| `avancado` | Tese central, frameworks mentais, análise crítica, interconexões |
| `metacognitivo` | Reflexão profunda, tensões, impacto pessoal |

---

## Como funciona

### Pipeline

```
URL ou arquivo
      │
      ├─ YouTube? ──▶ yt-dlp extrai legenda VTT (com timestamps)
      │                  │ sem legenda disponível?
      │                  └──▶ download de áudio ──▶ Groq Whisper API
      │
      ├─ Arquivo local? ──▶ Groq Whisper API
      │
      ▼
Transcrição completa
      │
      │ texto longo? (> 8k tokens)
      └──▶ divide em partes ──▶ resume cada uma via LLM ──▶ junta os resumos
      │
      ▼
LLaMA 3.3 70B  ←── rate limit (429)? fallback para LLaMA 3.1 8B
      │
      ▼
Preenche template Markdown com metadados do vídeo
      │
      ▼
Salva nota no output definido (padrão: data/04. notes/)
```

### Cache de transcrição

Se o JSON de transcrição já existe em disco para aquele vídeo, o pipeline pula o download e reutiliza o arquivo. Útil para regenerar notas com depth diferente ou template atualizado sem gastar tokens à toa.

### Resiliência em dois níveis

O chunking resolve transcrições longas demais para um único call. O fallback de modelo resolve rate limit durante a execução. Os dois juntos fazem vídeos de 1h+ funcionarem de forma confiável no free tier da Groq.

---

## Arquitetura

```
src/
├── cli.py              # Entry point — mtn youtube / mtn local (Typer)
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
data/                   # Runtime — gitignored
  02. audio/
  03. transcriptions/
  04. notes/
```

> `pydub` e `moviepy` são importados com lazy import para evitar quebra no Python 3.13 (módulo `audioop` removido). `HumanMessage` é usado diretamente em vez de `ChatPromptTemplate` para evitar conflito com `{variáveis}` em transcrições de código.

---

## Testes

```bash
poetry run pytest                          # todos os 102 testes
poetry run pytest -v                       # verbose
poetry run pytest tests/test_notes2_utils.py  # módulo específico
```

Cobre: geração de nota, chunking, fallback de modelo, cache de transcrição, split por capítulos, VTT parsing, CLI, templates e configuração de encoding.

---

## Roadmap

| Funcionalidade | Status |
|----------------|--------|
| Pipeline YouTube + arquivos locais | ✅ |
| 4 templates de profundidade | ✅ |
| Chunking automático para vídeos longos | ✅ |
| Fallback de modelo em rate limit | ✅ |
| VTT com timestamps para split por capítulo | ✅ |
| Flag `--by-chapter` | ✅ |
| Cache de transcrição | ✅ |
| 102 testes unitários | ✅ |
| Enricher — busca notas relacionadas no vault antes do LLM | 🔭 v2 |
| `--editorial` — passagem analítica antes de gerar a nota | 🔭 v2 |

---

## Licença

MIT
