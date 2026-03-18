---
page: "[[Análise Técnica]]"
Área:
  - Programação
tags:
  - Programação/Desenvolvimento
  - Programação/Qualidade
  - Análise
projeto: "[[Media to Notes]]"
data_nota: 2026-03-13
status: inbox
revisao:
---

# Análise Técnica — Media to Notes
[[📽️ Video to Notes - Automatizar Escolha de Templates de Notas e suas profundidades no assunto]]

> Análise feita com visão de engenheiro sênior. Cobre arquitetura, qualidade de código, segurança, testes, portabilidade e roadmap de expansão.

---

## 1. Visão Geral da Arquitetura

### O que existe

```
src/
├── core/          → lógica de negócio (audio, notes, notes2, converter, file_handler)
├── services/      → integrações externas (youtube, transcription, mongo)
├── interfaces/    → UIs (app_youtube.py, local-videos.py)
├── utils/         → utilitários (utils.py com print_hex_color)
├── tests/         → scripts de execução (não são testes unitários reais)
└── prompts.py     → prompt hardcoded para notas de curso
```

### Avaliação da estrutura

A separação em `core/`, `services/`, `interfaces/` é **conceitualmente correta** e mostra intenção arquitetural boa. O problema é que essa separação **não está sendo respeitada na prática**:

- `utils.py` tem funções de DWG/arquivos que não pertencem a esse projeto (`copiar_arquivos_para_temp`, `mover_arquivos`, `listar_arquivos` com DWG filter) — **vazamento de código de outro projeto (DWG Explorer)**.
- `notes.py` e `notes2.py` coexistem sem documentação de qual usar. São dois sistemas de geração de notas em paralelo — `notes.py` é o legado, `notes2.py` é o atual com templates. Isso é dívida técnica acumulada.
- `interfaces/app_youtube.py` usa `from services.youtube import *` sem o prefixo `src.`, o que quebra dependendo do diretório de execução.

---

## 2. Problemas Críticos (🔴 Bloqueia produção)

### 2.1 Paths absolutos hardcoded

**Arquivos afetados:** `notes2.py`, `test_youtube.py`, `test_notes.py`

```python
# notes2.py — linha 133-134 (bloco __main__)
path_transcricao_json="D:\\Users\\Lucas\\OneDrive\\...",
path_template_md="D:\\Users\\Lucas\\OneDrive\\..."

# test_youtube.py — linha 51
path_template_md="D:\\Users\\Lucas\\OneDrive\\..."
```

**Problema:** O código não roda em nenhuma outra máquina nem em outro diretório. Inviabiliza colaboração, CI/CD e deploy.

**Solução:** Usar `pathlib.Path(__file__).parent` para construir caminhos relativos ao projeto, ou variável de ambiente `VAULT_PATH`, `PROJECT_ROOT`.

---

### 2.2 Separadores de path misturados e Windows-only

**Arquivos afetados:** `audio.py`, `notes.py`, `notes2.py`, `transcription.py`, `test_youtube.py`

```python
# notes.py — linha 107
caminho_nota = "\\".join(text.replace("03. transcrições", "04. notas").split("\\")[:-1])

# transcription.py — linha 70
with open("transcricao_final.txt", "w", ...) # salva no CWD sem controle
```

O código mistura `\\`, `/` e `os.path.join` arbitrariamente. Não funciona em Linux/macOS. A substituição de strings para navegar entre pastas (`replace("03. transcrições", "04. notas")`) é especialmente frágil — qualquer rename de pasta quebra silenciosamente.

**Solução:** Usar `pathlib.Path` exclusivamente em todo o projeto.

---

### 2.3 Fallback de transcrição quebrado — `break` em vez de `continue`

**Arquivo:** `test_youtube.py` (que na prática é a pipeline principal), linhas 29-30

```python
if transcript:
    final_transcript = {...}
else:
    print_hex_color('#f92f60', "❌ Não foi possível extrair o transcript.")
    break  # ← ERRADO: para o loop inteiro
    # o código de fallback (Whisper) abaixo do break é código morto
```

Quando um vídeo não tem legenda disponível, o `break` para o processamento de **todos os vídeos restantes da lista**. O fallback via Whisper (que é o propósito do `transcrever_audio_inteligente`) nunca é executado — é código morto. Deveria ser `continue` + fallback real.

---

### 2.4 `arquivo_mais_recente` quebrada em `file_handler.py`

```python
# linha 66
arquivo = df_arquivos[0]  # KeyError garantido
```

`df_arquivos[0]` em um DataFrame pandas acessa a **coluna "0"**, que não existe. Deveria ser `df_arquivos.iloc[0]`. Função inutilizável no estado atual.

---

## 3. Problemas de Segurança (🟠 Risco real)

### 3.1 Gerenciamento de API Keys

**Arquivo:** `notes.py`, linhas 74-77

```python
load_dotenv()
api_key = os.getenv('GROQ_API_KEY')
os.environ['GROQ_API_KEY'] = api_key  # ← redundante e arriscado
chat = ChatGroq(model='llama-3.3-70b-versatile')
```

Dois problemas:
1. `os.environ['GROQ_API_KEY'] = api_key` é redundante — `load_dotenv()` já popula `os.environ`. Pior: se `api_key` for `None` (key não encontrada), isso silenciosamente seta `GROQ_API_KEY=None` como string, causando erro críptico na chamada da API.
2. Não há validação de que a key existe antes de usar.

**Verificação ausente:**
```python
# O que deveria existir:
if not api_key:
    raise ValueError("GROQ_API_KEY não encontrada. Verifique seu .env")
```

### 3.2 `.env` não está no `.gitignore`?

Não foi possível verificar o `.gitignore`, mas dado que o projeto usa `load_dotenv()` e tem `GROQ_API_KEY`, é essencial confirmar que `.env` está ignorado. Se o projeto estiver em repositório público, é um vazamento de credencial.

### 3.3 `from src.services.youtube import *` — wildcard import

**Arquivo:** `interfaces/app_youtube.py`

Wildcard imports (`*`) importam todo o namespace público do módulo, incluindo dependências transitivas. Dificulta auditoria de segurança, aumenta chance de colisão de nomes e torna difícil rastrear de onde cada função veio.

---

## 4. Qualidade de Código (🟡 Dívida técnica)

### 4.1 `print_hex_color` duplicada em 3 lugares

Definida em:
- `utils/utils.py`
- `services/transcription.py`
- `services/youtube.py`

Código idêntico, copiado. Qualquer bug ou melhoria precisa ser aplicada em 3 lugares. Deveria estar **apenas** em `utils.py` e importada nos outros.

### 4.2 JSON lido duas vezes em `notes.py`

```python
# notes.py — linhas 26-35
with open(text, "r", encoding="utf-8") as f:
    try:
        dados_transcricao = json.load(f)  # leitura 1 (com validação)
    except json.JSONDecodeError:
        ...

with open(text, "r", encoding="utf-8") as f:  # ← reabre desnecessariamente
    dados_transcricao = json.load(f)            # leitura 2 (sem validação)
```

O arquivo é aberto, lido e fechado duas vezes. A segunda leitura descarta o resultado da validação da primeira.

### 4.3 Dead code extenso

```python
# notes2.py — linhas 28-45 (comentado, mas não removido)
#ler = ler_md_template(...)
#print(ler[0])

# youtube.py — campos comentados com "Não usar"
#'channel_id': info.get('channel_id'),
#'view_count': info.get('view_count'),
```

Dead code comentado deve ser removido — o git guarda o histórico se precisar recuperar.

### 4.4 `gerar_capitulos_formatado` com bug silencioso

```python
# notes2.py — linhas 54-62
def gerar_capitulos_formatado(capitulos: list) -> str:
    linhas = []
    if capitulos:
        for cap in capitulos:
            ...
    else:
        resultado = ""  # ← definido aqui
    resultado = "\n".join(linhas)  # ← sempre sobrescreve, incluindo o else
    return resultado
```

A variável `resultado = ""` no `else` nunca tem efeito — é sobrescrita por `"\n".join(linhas)` que retorna `""` de qualquer forma quando `linhas` está vazia. O código funciona, mas a lógica é confusa.

### 4.5 Template com prompt no corpo do markdown

**Arquivo:** `templates/template_youtube.md`

```markdown
---
(frontmatter)
---
Atue como um especialista em síntese de informações...  ← isso é o prompt
## Resumo:
...
```

O prompt está no corpo do template. Quando o LLM gera a nota, essa instrução pode vazar para o output final. O `notes2.py` passa o prompt inteiro para o LLM, que deveria ignorá-lo — mas dependendo do modelo, pode incluir fragmentos no output.

**Melhor abordagem:** separar prompt (para o LLM) de template (estrutura da nota) em arquivos distintos.

### 4.6 `processar_links(Links)` executado no nível de módulo

**Arquivo:** `interfaces/app_youtube.py` (o script de pipeline), linha 152

```python
processar_links(Links)  # ← executa ao ser importado
```

Sem guard `if __name__ == "__main__"`. Qualquer import deste módulo (inclusive pelo pytest) dispara o processamento real de dezenas de URLs do YouTube com delays de 60-120s. Impossível testar.

---

## 5. Testes (🔴 Não existem testes reais)

### Estado atual

Os arquivos em `src/tests/` **não são testes unitários** — são scripts de execução:

| Arquivo | O que realmente faz |
|---------|-------------------|
| `test_transcription.py` | Executa `transcrever_pasta` em dados reais de WhatsApp |
| `test_audio.py` | Lista e converte arquivos `.opus` reais |
| `test_notes.py` | Itera sobre transcrições reais e gera notas |
| `test_youtube.py` | É a pipeline principal de YouTube, com lista de links |
| `file_handler_test.py` | (não lido, mas provavelmente similar) |
| `test_converter.py` | (não lido) |

Nenhum desses arquivos usa `pytest`, `unittest` ou qualquer framework de testes. Não têm `assert`. Não podem ser rodados em CI/CD. Dependem de dados reais e chamadas de API.

### O que está faltando

**Testes unitários necessários (sem chamadas de API):**

```
✗ extract_video_id() — testar com URLs válidas, inválidas, shorts, playlists
✗ sanitize_filename() — caracteres especiais, acentos, strings longas
✗ gerar_capitulos_formatado() — lista vazia, lista com dados, None
✗ preencher_variables() — chaves presentes, ausentes, aninhadas
✗ ler_md_template() — frontmatter válido, sem frontmatter, com --- no corpo
✗ transcript_to_text() — lista vazia, lista com dados
✗ cortar_audio_hibrido() — modo inválido (testa o raise ValueError)
```

**Testes de integração necessários (com mocks):**

```
✗ get_video_metadata() — mock do yt-dlp
✗ transcrever_audio() — mock do Groq client
✗ gerar_nota_md() — mock do LLM, verifica output do arquivo
✗ salvar_transcricao() — verifica JSON salvo
```

### Como rodar o que existe

```bash
# Não use pytest — vai executar código real
# Cada arquivo é um script:
poetry run python src/tests/test_youtube.py
```

---

## 6. Portabilidade e Escalabilidade

### 6.1 Limitação para vídeos longos — causa real

O projeto usa Groq Whisper API com limite de **25 MB por arquivo**. A solução de chunking (`cortar_audio_hibrido`) existe, mas tem problemas:

1. O fallback em `Youtube_to_Notes` tem `break` em vez de ativá-lo (seção 2.3)
2. `transcrever_audio_inteligente` junta os chunks em texto bruto — perde timestamps e segmentos
3. O resultado não tem o mesmo formato que a transcrição direta (retorna `{"text": texto}` sem `segments`)
4. Arquivo salvo em `transcricao_final.txt` no CWD — sem controle de onde vai parar

**Para vídeos longos funcionarem de verdade:**
- Corrigir o `break` → `continue` + ativar o fallback
- Manter timestamps ao juntar chunks (propagar `start` offset de cada chunk)
- Retornar formato consistente com a transcrição direta

### 6.2 Rate limiting manual com `time.sleep` random

```python
delay = random.uniform(60, 120)
time.sleep(delay)  # 1-2 minutos entre vídeos
```

Funciona, mas é primitivo. Para processar a lista atual (dezenas de vídeos), leva horas bloqueando o processo. Sem retry em caso de erro, sem backoff exponencial.

### 6.3 MongoDB planejado mas não integrado

`pipeline_model.py` e `mongodb.py` existem mas não são usados em nenhum lugar da pipeline principal. A pipeline ainda salva tudo em arquivos JSON no disco. O roadmap de MongoDB está no README mas o código está numa fase de "planejado".

---

## 7. Dependências

### Dependências de dev em produção

```toml
# pyproject.toml — em dependencies (produção):
"ipykernel (>=6.29.5,<7.0.0)",
"jupyter (>=1.1.1,<2.0.0)",
"openpyxl (>=3.1.5,<4.0.0)",
```

Jupyter e ipykernel não têm papel em produção — pertencem a `[tool.poetry.group.dev.dependencies]`. Isso aumenta o tamanho do ambiente desnecessariamente.

### `dotenv` vs `python-dotenv`

O `pyproject.toml` lista `dotenv (>=0.9.9)`, mas o código usa `from dotenv import load_dotenv`. O pacote PyPI correto é `python-dotenv`, não `dotenv` (que é um pacote diferente). Verificar qual está instalado no ambiente: `pip show python-dotenv`.

---

## 8. Resumo por Severidade

| # | Problema | Severidade | Arquivo(s) |
|---|---------|-----------|-----------|
| 1 | Fallback Whisper nunca executa (`break`) | 🔴 Crítico | `test_youtube.py:29` |
| 2 | Paths absolutos hardcoded | 🔴 Crítico | `notes2.py`, `test_youtube.py` |
| 3 | `arquivo_mais_recente` quebrada (`df[0]`) | 🔴 Crítico | `file_handler.py:66` |
| 4 | API key sem validação (None silencioso) | 🟠 Segurança | `notes.py:74` |
| 5 | `processar_links` executa ao importar | 🟠 Alto | `app_youtube.py:152` |
| 6 | Wildcard imports | 🟠 Médio | `app_youtube.py:2` |
| 7 | Separadores Windows-only | 🟡 Portabilidade | múltiplos |
| 8 | `print_hex_color` duplicada 3x | 🟡 Manutenção | múltiplos |
| 9 | JSON lido duas vezes | 🟡 Qualidade | `notes.py:26-35` |
| 10 | `notes.py` vs `notes2.py` — dois sistemas | 🟡 Qualidade | ambos |
| 11 | Dead code extenso | 🟡 Qualidade | `notes2.py`, `youtube.py` |
| 12 | Sem testes unitários reais | 🟡 Qualidade | `src/tests/` |
| 13 | Jupyter/ipykernel em produção | 🟢 Baixo | `pyproject.toml` |
| 14 | MongoDB não integrado | 🟢 Roadmap | `services/mongo/` |

---

## 9. Roadmap de Correções Prioritárias

### Sprint 1 — Estabilizar o que existe (bugs críticos)

1. **Corrigir `break` → `continue` + ativar fallback Whisper** em `Youtube_to_Notes`
2. **Corrigir `arquivo_mais_recente`**: `df_arquivos[0]` → `df_arquivos.iloc[0]`
3. **Adicionar guard `if __name__ == "__main__"`** em `app_youtube.py`
4. **Validar API keys antes de usar**: raise explícito se `None`
5. **Consolidar `print_hex_color`**: remover das cópias, importar de `utils.py`

### Sprint 2 — Portabilidade e qualidade

6. **Migrar paths para `pathlib.Path`** em todo o projeto
7. **Remover `notes.py`**: consolidar em `notes2.py` (melhor) ou documentar a diferença
8. **Remover dead code** comentado
9. **Adicionar `.gitignore` explícito** para `.env`, `data/`, arquivos de áudio/vídeo

### Sprint 3 — Testes reais

10. **Criar testes unitários** com pytest para: `extract_video_id`, `sanitize_filename`, `preencher_variables`, `gerar_capitulos_formatado`, `ler_md_template`
11. **Mockar APIs** (Groq, yt-dlp) nos testes de integração
12. **Separar `tests/` de scripts de execução** — mover scripts para `scripts/` ou `notebooks/`

### Sprint 4 — Expansão para vídeos longos e artigos

13. **Corrigir pipeline de chunks**: propagar timestamps ao juntar, output consistente
14. **Adicionar modo `--source article`**: WebFetch + defuddle como input alternativo
15. **Integrar com vault Obsidian**: output direto para `_revisar/` em vez de `data/04. notes/`
16. **MongoDB**: integrar se realmente for usar, ou remover os arquivos de mock

---

## 10. Nota Final

O projeto tem **fundação sólida**: a ideia é clara, a separação de responsabilidades existe no papel, e a pipeline de YouTube → transcrição → nota funciona para o caso feliz (vídeo curto com legenda disponível). O Akita aprovaria a iniciativa — mas diria que o FrankMD aqui é o `test_youtube.py` com o `break` que nunca ativa o Whisper.

As correções do Sprint 1 são todas cirúrgicas e podem ser feitas em menos de 2 horas. O retorno é grande: a pipeline passa a funcionar para vídeos longos (a funcionalidade mais pedida no roadmap).
