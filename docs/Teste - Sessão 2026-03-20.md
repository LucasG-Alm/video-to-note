# Teste de Sessão — Media to Notes
**Data:** 2026-03-20
**Vídeo testado:** [O Método Fábio Akita para programar com IA](https://www.youtube.com/watch?v=cWY7iBafw7I) — canal Mano Deyvin (45min10s, 6 capítulos)
**Ambiente:** Windows 11, Python 3.13, Poetry, Groq free tier

---

## Resultado final

Pipeline parcialmente funcional. A transcrição foi obtida com sucesso via legendas do YouTube. A geração de nota falhou no fluxo padrão e precisou de workaround manual (processamento por capítulos). A nota final foi gerada e salva no vault.

---

## Erros encontrados

### ERR-01 — UnicodeEncodeError no Windows (emojis no terminal)
**Arquivo:** `src/utils/utils.py:5` e `src/pipeline.py:55`
**Categoria:** Bug — Compatibilidade de plataforma
**Urgência:** 🔴 Alta
**Impacto:** Alto — impede qualquer execução no Windows sem workaround

**O que aconteceu:**
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f3ac'
position 18: character maps to <undefined>
```
O terminal do Windows usa `cp1252` por padrão. A função `print_hex_color` recebe strings com emojis (ex: `"🎬 Processando:"`) e o `print()` tenta encodar com `cp1252`, que não suporta emojis.

**Workaround usado:** `PYTHONIOENCODING=utf-8` como variável de ambiente antes de rodar.

**Fix correto:** Adicionar `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` no início de `cli.py`, ou usar `errors='replace'` no `print()` de `print_hex_color`.

---

### ERR-02 — Groq TPM rate limit excedido
**Arquivo:** `src/core/notes2.py` (chamada ao LLM)
**Categoria:** Bug — Limitação de API
**Urgência:** 🔴 Alta
**Impacto:** Alto — bloqueia qualquer vídeo com transcrição > ~12k tokens (~45+ min)

**O que aconteceu:**
```
Error code: 413 - Request too large for model llama-3.3-70b-versatile
Limit 12000, Requested 14537
```
O modelo `llama-3.3-70b-versatile` no plano free da Groq tem limite de 12k TPM. O vídeo de 45min gerou 14.5k tokens de transcrição — excede o limite sem chunking.

**Workaround usado:** Processamento manual por capítulos (script ad-hoc), cada capítulo enviado separadamente (máximo ~3.3k tokens por chunk).

**Fix correto:** Adicionar lógica de chunking automático em `notes2.py`:
1. Estimar token count da transcrição antes de enviar
2. Se exceder limite configurável (padrão: 10k), dividir por capítulos (se disponíveis) ou por palavras
3. Processar cada chunk e concatenar os resultados antes de montar a nota final

---

### ERR-03 — `find_dotenv()` assertion error via heredoc/stdin
**Arquivo:** `src/core/notes2.py:93` — `load_dotenv()`
**Categoria:** Bug — Ambiente de execução
**Urgência:** 🟡 Média
**Impacto:** Médio — afeta scripts ad-hoc e testes fora do contexto normal da CLI

**O que aconteceu:**
```
AssertionError: frame.f_back is not None
```
`find_dotenv()` sem argumentos percorre o call stack para encontrar o `.env`. Quando executado via bash heredoc (`<< 'EOF'`) ou stdin, o frame de chamada não existe e a assertion falha.

**Workaround usado:** Passar `GROQ_API_KEY` diretamente como variável de ambiente no shell.

**Fix correto:** Em `notes2.py`, substituir `load_dotenv()` por `load_dotenv(Path(__file__).parent.parent / '.env')` com caminho explícito.

---

### ERR-04 — Segments da transcrição sem timestamps
**Arquivo:** `src/services/youtube.py` (extração via yt-dlp)
**Categoria:** Limitação — YouTube / yt-dlp
**Urgência:** 🟡 Média
**Impacto:** Médio — impede divisão precisa por capítulos, força workaround proporcional

**O que aconteceu:**
Todos os 1.326 segments da transcrição vieram com `start: 0.0, duration: 0.0`. As legendas do YouTube via yt-dlp não estavam preservando timestamps no formato esperado pelo pipeline.

**Workaround usado:** Divisão proporcional do texto completo baseada nos percentuais de tempo de cada capítulo (ex: capítulo começa em 19% da duração total → começa em 19% dos caracteres totais). Aproximação funcional mas imprecisa.

**Fix correto:** Investigar o formato de saída do yt-dlp para legendas com timestamps. Verificar se o campo `segments` tem subformato diferente dependendo do tipo de legenda (automática vs. manual). Considerar usar `--write-subs` + `--sub-format vtt` para obter timestamps precisos.

---

### WARN-01 — yt-dlp nsig extraction warnings
**Categoria:** Aviso — Dependência desatualizada
**Urgência:** 🟢 Baixa
**Impacto:** Baixo — alguns formatos de vídeo podem não estar disponíveis

**O que aconteceu:**
```
WARNING: nsig extraction failed: Some formats may be missing
YouTube is forcing SABR streaming for this client
```
yt-dlp está desatualizado. O YouTube mudou o protocolo de streaming e versões antigas do yt-dlp não conseguem extrair todos os formatos.

**Fix correto:** `poetry run pip install -U yt-dlp` e adicionar isso às instruções de manutenção no CLAUDE.md.

---

## Adaptações que funcionaram

### ADAP-01 — Processamento por capítulos
Dividir a transcrição em capítulos e processar cada um separadamente com o LLM resolve tanto o problema de token limit quanto melhora a qualidade da nota (cada seção recebe atenção focada). Deveria virar funcionalidade nativa da CLI.

### ADAP-02 — Análise editorial antes de gerar nota
Rodar uma passagem de análise por capítulo (como editor de jornal) antes de gerar a nota final revelou pontos fortes, fracos e lacunas do conteúdo. Isso é informação valiosa que poderia aparecer numa seção "Avaliação editorial" da nota `avancado` e `metacognitivo`.

### ADAP-03 — Enriquecimento com notas do vault
Injetar contexto das notas existentes no vault (sobre Akita, XP, TDD) no prompt final produziu uma nota mais conectada e precisa. O pipeline deveria ter uma etapa opcional de "busca no vault" antes de gerar a nota.

---

## Melhorias identificadas

| ID | Descrição | Categoria | Urgência | Impacto |
|----|-----------|-----------|----------|---------|
| M-01 | Fix encoding UTF-8 no CLI entry point (`cli.py`) | Bug fix | 🔴 Alta | Alto |
| M-02 | Chunking automático de transcrição longa por capítulos | Bug fix | 🔴 Alta | Alto |
| M-03 | `load_dotenv()` com path explícito em `notes2.py` | Bug fix | 🟡 Média | Médio |
| M-04 | Investigar timestamps nos segments do yt-dlp | Bug fix | 🟡 Média | Médio |
| M-05 | Flag `--by-chapter` na CLI para processar por capítulos | Feature | 🟡 Média | Alto |
| M-06 | Análise editorial como etapa opcional do pipeline | Feature | 🟢 Baixa | Alto |
| M-07 | Etapa de enriquecimento via vault Obsidian antes do LLM | Feature | 🟢 Baixa | Alto |
| M-08 | Atualizar yt-dlp (`poetry run pip install -U yt-dlp`) | Manutenção | 🟢 Baixa | Baixo |
| M-09 | Estimativa de tokens antes de chamar o LLM (com aviso) | UX | 🟡 Média | Médio |
| M-10 | Fallback automático de modelo quando TPM excedido | Resiliência | 🟡 Média | Alto |
