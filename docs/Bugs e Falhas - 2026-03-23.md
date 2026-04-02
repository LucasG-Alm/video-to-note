# Bugs, Falhas e Sucessos — Sessões 2026-03-22 e 2026-03-23

> Documento gerado ao final da Sprint 2. Registra o que foi corrigido, o que falhou e o que ainda precisa de atenção.

---

## ✅ Sucessos

### Sprint 1 (2026-03-22)

| ID | O que foi | Como resolveu |
|----|-----------|---------------|
| ERR-01 | UnicodeEncodeError no Windows (emojis quebravam no terminal cp1252) | `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` no topo de `cli.py` |
| ERR-02 | Groq TPM limit em vídeos longos (>~45min) | Chunking automático em `notes2.py`: estima tokens, divide em chunks de 5k, resume cada parte, gera nota final a partir dos resumos |
| ERR-03 | `load_dotenv()` falhava via stdin/heredoc | `load_dotenv(Path(__file__).parent.parent.parent / '.env')` — caminho absoluto explícito |
| ERR-04 | Segments de transcrição sem timestamps (start: 0.0) | VTT parsing implementado em `youtube.py`: `_vtt_time_to_seconds`, `_parse_vtt`, `_parse_json3`; pipeline prefere VTT e cai no json3 como fallback |
| M-08 | yt-dlp desatualizado + yt-dlp-ytse incompatível com yt-dlp 2026.x | Atualizado para `>=2026.3.17`, removido yt-dlp-ytse (nsig agora nativo no yt-dlp) |

### Sprint 2 (2026-03-23)

| ID | O que foi | Como resolveu |
|----|-----------|---------------|
| M-09 | Sem aviso quando prompt está próximo do limite | `_warn_if_tokens_high`: estima tokens e imprime aviso se >10k |
| M-10 | Sem fallback quando TPM excedido | `_invoke_llm_with_fallback`: detecta erro 429 (TPM) e reexecuta com `llama-3.1-8b-instant` |
| M-05 | Sem suporte a processamento por capítulo | `--by-chapter` no CLI + `_gerar_nota_por_capitulos` no pipeline + `split_transcript_by_chapters` em `notes2.py` |

### Validação real

- Vídeo de 60min (Israel Subira) processado com sucesso: 40.888 tokens estimados → 9 chunks → nota gerada
- Vídeo de 13min (WhisperX) processado com sucesso via fallback 8b (TPD estourado)
- 95 testes automatizados passando após Sprint 2

---

## 🐛 Bugs Conhecidos (não corrigidos)

### BUG-01 — `_summarize_chunk` não usa fallback de modelo

**Onde:** `src/core/notes2.py` → `_summarize_chunk`

**Problema:** As chamadas de chunking usam `(prompt | chat).invoke(...)` diretamente, sem passar por `_invoke_llm_with_fallback`. Quando o TPM ou TPD estoura *durante* o chunking, a exceção sobe imediatamente sem tentar o modelo 8b.

**Efeito prático:** Vídeos longos (que precisam de chunking) não se beneficiam do M-10. Só o call final em `gerar_nota_md` tem fallback.

**Fix sugerido:** Refatorar `_summarize_chunk` para aceitar `api_key` e usar `_invoke_llm_with_fallback` internamente, ou criar uma versão do chunking que use `HumanMessage` direto como o resto do código.

```python
# Atual (sem fallback)
def _summarize_chunk(chunk, chat, idx, total):
    prompt = ChatPromptTemplate.from_template(...)
    result = (prompt | chat).invoke(...)

# Sugerido
def _summarize_chunk(chunk, primary_model, fallback_model, api_key, idx, total):
    prompt_text = f"Resuma... ({idx} de {total}):\n\n{chunk}"
    return _invoke_llm_with_fallback(prompt_text, primary_model, fallback_model, api_key)
```

---

### BUG-02 — `mtn youtube` sempre re-transcreve, ignora JSON existente

**Onde:** `src/pipeline.py` → `youtube_to_notes`

**Problema:** O pipeline sempre executa o fluxo completo (fetch metadados → download legenda → salva JSON → gera nota), mesmo que um JSON de transcrição já exista em disco para aquele vídeo.

**Efeito prático:** Re-download desnecessário de legendas; impossível "só regenerar a nota" a partir de transcrição existente via CLI.

**Fix sugerido:** Verificar se o JSON já existe antes de transcrever:

```python
json_path = PROJECT_ROOT / "data/03. transcriptions/Youtube" / f"{title}.json"
if json_path.exists():
    print_hex_color('#32cbff', "♻️  Transcrição existente encontrada, pulando download.", "")
    with open(json_path) as f:
        saved = json.load(f)
    final_transcript = saved.get('transcription', {})
    metadata = saved.get('metadata', {})
else:
    # fluxo normal de download
    ...
```

---

### BUG-03 — `data_nota` sempre gerada com a data atual

**Onde:** `src/core/notes2.py` → `gerar_nota_md`

**Problema:** `data_atual = datetime.now().strftime(...)` é hardcoded e sobrescreve qualquer valor passado via `metadata`. Não tem como injetar uma data customizada pelo pipeline.

**Efeito prático:** Ao gerar notas de transcrições antigas (ex: 2025-07-12), o campo `data_nota` na nota fica com a data de hoje. Workaround atual: post-processing com regex após a geração.

**Fix sugerido:** Adicionar parâmetro opcional `date_override` em `gerar_nota_md`:

```python
def gerar_nota_md(..., date_override: str = None):
    data_atual = date_override or datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
```

---

## ⚠️ Limitações de Infraestrutura (Groq free tier)

### LIMIT-01 — TPD (Tokens Per Day): 100.000 tokens/dia por modelo

**O que é:** Limite diário independente do TPM. Se o TPD de `llama-3.3-70b-versatile` esgotar, todos os calls falham com 429 até o reset (janela deslizante de ~24h).

**Efeito prático:**
- Um vídeo de 60min consome ~50k tokens (chunking + nota final)
- Dois vídeos longos = dia inteiro de quota esgotada
- `_invoke_llm_with_fallback` detecta o 429 e tenta 8b, mas o 8b também tem seu próprio TPD

**O que investigar na documentação da Groq:**
- Limites exatos por modelo (70b vs 8b vs outros)
- Se TPD é por modelo ou compartilhado entre modelos
- Modelos alternativos com limites maiores (ex: `mixtral-8x7b-32768`, `gemma2-9b-it`)
- Plano Dev: quanto custa, qual o TPD

**Possíveis estratégias:**
1. Alternar entre modelos para distribuir carga (70b → 8b → outro modelo)
2. Processar no máximo 1-2 vídeos longos por dia no free tier
3. Cache de resumos de chunks: se o chunk já foi resumido antes, não re-chamar a API

---

## 📋 Backlog gerado a partir desta análise

| ID | Descrição | Prioridade |
|----|-----------|-----------|
| FIX-01 | Refatorar `_summarize_chunk` para usar `_invoke_llm_with_fallback` | Alta |
| FIX-02 | Cache de transcrição: pular download se JSON já existe | Média |
| FIX-03 | Parâmetro `date_override` em `gerar_nota_md` | Média |
| INV-01 | Investigar limites reais da Groq (TPD por modelo, plano Dev) | Alta |
| INV-02 | Avaliar modelos alternativos com maior quota gratuita | Média |
