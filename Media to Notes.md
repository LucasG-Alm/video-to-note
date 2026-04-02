---
tags:
  - Projetos/Programação
tipo: projeto
categoria: Programação
status: ativo
tasks_done: 1
tasks_total: 9
proxima_acao: "Processar 64 vídeos pendentes em `_videos em processamento` (await TPM reset Groq)"
github: "https://github.com/LucasG-Alm/video-to-note"
revisao: 2026-03-24
---

# Media to Notes

CLI tool (`mtn`) que converte vídeos do YouTube e arquivos locais de áudio/vídeo em notas Markdown estruturadas. Pipeline: URL/arquivo → Groq Whisper (transcrição) → LangChain + Groq LLM → nota com template por profundidade.

## Estado atual

**v0.2.0 — CLI Refatorado (02/04/2026)**

CLI simplificado com auto-dispatch: `mtn "<url>"` detecta automaticamente YouTube vs arquivo local. Comando `config` para gerenciar DEFAULT_OUTPUT_DIR. 126 testes passando (24 novos). Skill atualizada com confirmação + pergunta de profundidade.

Pipeline estável. Sprint Assets/Publicação + Sprint Qualidade 🟡 no backlog.

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

- [ ] ERR-02: Groq TPM limit em vídeos longos — dividir por capítulos/blocos, processar por partes
- [ ] ERR-04: timestamps zerados nas legendas automáticas do YouTube — investigar `--write-subs --sub-format vtt`
- [ ] M-06: Análise editorial como etapa opcional (`--editorial`)
- [ ] M-07: Enriquecimento via vault Obsidian: buscar notas relacionadas antes do LLM
- [ ] M-08: Atualizar yt-dlp (`poetry run pip install -U yt-dlp`)
- [ ] Enricher como comando Obsidian (v2) — ver `docs/Ideia - Enricher como Comando Obsidian.md`

## Decisões tomadas

- Profundidade via flag `--depth`: raso / intermediario (default) / avancado / metacognitivo
- Templates Markdown por nível em `templates/`
- `pydub` e `moviepy` com import lazy (quebra Python 3.13 se no topo do arquivo)
- Venv fora do OneDrive: `AppData\Local\pypoetry\Cache\virtualenvs\`

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
