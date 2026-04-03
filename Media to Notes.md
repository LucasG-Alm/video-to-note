---
tags:
  - Projetos/Programação
tipo: projeto
categoria: Programação
status: ativo
tasks_done: 1
tasks_total: 9
proxima_acao: "Fix NotebookLM E2E: subprocess encoding (PYTHONIOENCODING=utf-8) + trocar shell=True por lista de args"
github: "https://github.com/LucasG-Alm/video-to-note"
revisao: 2026-03-24
---

# Media to Notes

CLI tool (`mtn`) que converte vídeos do YouTube e arquivos locais de áudio/vídeo em notas Markdown estruturadas. Pipeline: URL/arquivo → Groq Whisper (transcrição) → LangChain + Groq LLM → nota com template por profundidade.

## Estado atual

**v0.3.0-dev — NotebookLM Integration (03/04/2026)**

Integração NotebookLM implementada (Tasks 0-3): pipeline detecta vídeos longos (>30min) com capítulos e tenta resumir por NotebookLM antes de usar Groq. Graceful fallback preservado. 7 commits, 16 testes novos (136 total). E2E ainda pendente — bugs de encoding Windows no CLI notebooklm bloqueiam o fluxo.

Pipeline estável com fallback. Sprint Assets/Publicação + Sprint Qualidade 🟡 no backlog.

## Tasks — Sprint atual (Assets + Publicação)

- [ ] Preparar apresentação/post sobre sessões 22-23/03 → **SHARE**
- [ ] Criar `assets/icon.png` (128×128px, microfone + folha Markdown)
- [ ] Criar `assets/demo.gif` (ScreenToGif: `mtn youtube <url>` até `✅ Nota gerada`)
- [ ] Criar `assets/note-preview.png` (nota no Obsidian tema dark)
- [ ] Criar `assets/depths.png` (4 níveis de profundidade side-by-side)
- [ ] Revisar README.md e publicar no GitHub após assets prontos
- [ ] Processar 64 vídeos pendentes em `_videos em processamento` (aguardar reset TPD Groq)
- [ ] INV-01: ler doc Groq — limites TPD por modelo, Dev tier pricing
- [x] ✅ Refatorar o CLI usando o descritivo em [[issues-cli_update]] (concluído em 02/04)

## Tasks — Sprint Qualidade 🟡 Média prioridade

> Executar antes ou durante a próxima feature. Não bloqueia publicação do README mas bloqueia escalar o projeto.

- [ ] Rodar `pytest --cov=src --cov-report=term-missing` e documentar % de cobertura atual
- [ ] Identificar funções que misturam lógica + I/O em `pipeline.py` e extrair as puras
- [ ] Injetar `GroqClient` e `Downloader` via parâmetro onde ainda estão hardcoded
- [ ] Adicionar 3 testes property-based: parser de URL do YouTube, `truncar_texto`, `parsear_transcricao`

## Backlog

- [ ] **NLM-01:** Fix encoding Windows no subprocess — rodar `notebooklm` com `env={"PYTHONIOENCODING": "utf-8"}` no subprocess
- [ ] **NLM-02:** Fix shell quoting — trocar `shell=True` por lista de args `["notebooklm", "ask", query, "-n", nb_id, "--json"]`
- [ ] **NLM-03:** E2E test completo após NLM-01 + NLM-02 corrigidos — validar resumo por capítulos funcionando
- [ ] ERR-02: Groq TPM limit em vídeos longos — dividir por capítulos/blocos, processar por partes
- [ ] ERR-04: timestamps zerados nas legendas automáticas do YouTube — investigar `--write-subs --sub-format vtt`
- [ ] M-06: Análise editorial como etapa opcional (`--editorial`)
- [ ] M-07: Enriquecimento via vault Obsidian: buscar notas relacionadas antes do LLM
- [ ] M-08: Atualizar yt-dlp (`poetry run pip install -U yt-dlp`)
- [ ] Enricher como comando Obsidian (v2) — ver `docs/Ideia - Enricher como Comando Obsidian.md`

## Decisões tomadas

| Data | Decisão |
|------|---------|
| 2026-04-03 14:00 | Usar `notebooklm` CLI via subprocess em vez de lib Python diretamente — mais simples, sem gerenciar sessão async |
| 2026-04-03 14:00 | Reusable notebook pattern: 1 notebook por usuário, troca source por vídeo via `NOTEBOOKLM_LAST_SOURCE_ID` |
| 2026-04-03 14:00 | Graceful fallback: qualquer erro no bloco NotebookLM cai silenciosamente pra Groq — nada quebra pra usuário |
| 2026-04-03 14:00 | Condição de entrada NotebookLM: `is_long_video() AND chapters` — sem capítulos vai direto pra Groq |
| — | Profundidade via flag `--depth`: raso / intermediario (default) / avancado / metacognitivo |
| — | Templates Markdown por nível em `templates/` |
| — | `pydub` e `moviepy` com import lazy (quebra Python 3.13 se no topo do arquivo) |
| — | Venv fora do OneDrive: `AppData\Local\pypoetry\Cache\virtualenvs\` |

## Publicação

- **GitHub:** sim — https://github.com/LucasG-Alm/video-to-note
- **Notion:** não
- **LinkedIn/Instagram:** sim (via LKE — sessões 22-23/03 são conteúdo)

## Referências

- [[Media to Notes/CLAUDE.md]]
- `docs/Teste - Sessão 2026-03-20.md`

## Histórico de Sessões

| Data | Resumo | Relatório |
|------|--------|-----------|
| 2026-03-22 | ERR-01 a ERR-04 corrigidos com TDD (102 testes), cache de transcrição, README reescrito | [[S2026-03-22 - Media to Notes]] |
| 2026-03-23 | Sprint 2: M-09 (token warning) + M-10 (fallback 70b→8b) + M-05 (--by-chapter) — 95 testes | [[S2026-03-23-2 - Media to Notes]] |
| 2026-03-24 | Nota de projeto criada do zero; Sprint Qualidade 🟡 criada (DI, cobertura, property-based); Hexagonal descartado | [[S2026-03-24 - Qualidade de Testes]] |
| 2026-04-01 | Documentação de CLI atualizada (pip install -e, removido poetry run); refatoração do CLI agendada | [[S2026-04-01 - Media to Notes - CLAUDE]] |
| 2026-04-02 | CLI refatorado: auto-dispatch `mtn "<input>"`, comando `config`, input_detector.py (24 testes novos); fix DEFAULT_OUTPUT_DIR; 6 vídeos processados (5/6); notas em `_revisar/YouTube/` | [[S2026-04-02 - Media to Notes - CLAUDE]] |
| 2026-04-02 | **Spec NotebookLM-py:** Planejamento TDD (6 tasks) pra integrar NotebookLM como solução ERR-02 (vídeos longos). Fallback gracioso, pragmatismo MVP. Pronto pra implementação subagent-driven | [[S2026-04-02-2 - Media to Notes - CLAUDE]] |
| 2026-04-03 | **Implementação NotebookLM (Tasks 0-3):** 7 commits, 16 testes novos, pipeline com fallback gracioso. E2E travou em bugs de encoding Windows + shell quoting no CLI notebooklm | [[S2026-04-03 - Media to Notes - CLAUDE]] |
