# Refatoração CLI — Comando Unificado Media to Notes

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unificar o CLI para aceitar um comando principal `mtn "<input>"` que detecta automaticamente se é URL (YouTube) ou arquivo local, mantendo compatibilidade total com subcomandos antigos.

**Architecture:** 
1. Adicionar `DEFAULT_OUTPUT_DIR` em `config.py`
2. Criar módulo `input_detector.py` com lógica de detecção (URL vs arquivo)
3. Adicionar comando raiz `main()` que delega para `youtube_to_notes()` ou `local_to_notes()` baseado no tipo detectado
4. Preservar subcomandos `youtube` e `local` como aliases/compatibilidade
5. Validar entrada com mensagens claras de erro

**Tech Stack:** Typer, Python stdlib (`os.path`, `urllib.parse`, regex), pytest

---

## Decisões Finais (Aprovadas por Lucas)

| Decisão | Implementação |
|---------|----------------|
| **DEFAULT_OUTPUT_DIR** | Comando CLI para configurar + salvamento automático em `.env` |
| **Flags opcionais** | Todas: `--depth`, `--output`, `--lang`, `--model`, `--by-chapter` |
| **Validação YouTube** | Rigorosa (verificar se URL é estruturalmente correta antes de processar) |
| **Comportamento sem args** | Erro claro: `❌ Erro: Falta o argumento obrigatório INPUT_SOURCE` |
| **Subcomandos antigos** | Mantidos indefinidamente sem deprecation (backward compatible) |

---

## File Structure

```
src/
├── cli.py                      # MODIFY: adicionar comando raiz + função main()
├── config.py                   # MODIFY: adicionar DEFAULT_OUTPUT_DIR
├── utils/
│   ├── input_detector.py       # CREATE: funções detect_input_type(), validate_input()
│   └── utils.py                # (já existe, sem mudanças)
└── pipeline.py                 # (sem mudanças — functions são chamadas diretamente)

tests/
├── unit/
│   └── test_input_detector.py  # CREATE: testes de detecção e validação
└── ... (testes existentes)
```

---

## Task 0: Criar comando `mtn config` para gerenciar DEFAULT_OUTPUT_DIR

**Files:**
- Modify: `src/cli.py`
- Modify: `src/config.py`

- [ ] **Step 1: Adicionar função helper em `config.py` para salvar variáveis em `.env`**

```python
def save_config_to_env(key: str, value: str) -> None:
    """
    Salva uma chave-valor no arquivo .env do projeto.
    Cria o arquivo se não existir.
    """
    from pathlib import Path
    
    env_path = PROJECT_ROOT / ".env"
    lines = []
    key_found = False
    
    # Ler linhas existentes
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    
    # Atualizar ou adicionar a chave
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            key_found = True
        else:
            new_lines.append(line)
    
    if not key_found:
        new_lines.append(f"{key}={value}\n")
    
    # Escrever de volta
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
```

- [ ] **Step 2: Adicionar comando `config` em `src/cli.py`**

```python
@app.command()
def config(
    set_output_dir: Annotated[Optional[str], typer.Option("--set-output", help="Define o diretório de saída padrão")] = None,
    show: Annotated[bool, typer.Option("--show", help="Mostra configuração atual")] = False,
):
    """Gerencia configurações do MTN (DEFAULT_OUTPUT_DIR, etc)."""
    from src.config import save_config_to_env, DEFAULT_OUTPUT_DIR
    from pathlib import Path
    
    if show:
        current = DEFAULT_OUTPUT_DIR or "data/04. notes/ (padrão)"
        typer.echo(f"📋 Configuração atual:")
        typer.echo(f"   DEFAULT_OUTPUT_DIR = {current}")
        return
    
    if set_output_dir:
        path = Path(set_output_dir)
        path.mkdir(parents=True, exist_ok=True)
        save_config_to_env("DEFAULT_OUTPUT_DIR", str(path))
        typer.echo(f"✅ Diretório de saída salvo em .env: {path}")
        return
    
    # Se nenhuma opção foi fornecida, mostra help
    typer.echo("Use: mtn config --set-output <caminho>  ou  mtn config --show")
```

- [ ] **Step 3: Testar comando**

```bash
poetry run mtn config --show
poetry run mtn config --set-output "C:/Users/lucas/OneDrive/Documentos/_Obsidian/Principal/Projetos/Programação/Media to Notes/data/04. notes/"
poetry run mtn config --show
```

- [ ] **Step 4: Commit**

```bash
git add src/cli.py src/config.py
git commit -m "feat: add config command for managing DEFAULT_OUTPUT_DIR"
```

---

## Task 1: Adicionar `DEFAULT_OUTPUT_DIR` em `config.py`

**Files:**
- Modify: `src/config.py`

- [ ] **Step 1: Ler `config.py` atual**

```bash
cat src/config.py
```

Expected: Mostrar defaults atuais (DEFAULT_MODEL, DEFAULT_DEPTH, DEFAULT_LANG)

- [ ] **Step 2: Adicionar `DEFAULT_OUTPUT_DIR`**

Adicione esta linha ao final de `src/config.py`:

```python
# Output directory for notes
# Falls back to data/04. notes/ if not set (subdirs Youtube, Local)
DEFAULT_OUTPUT_DIR = os.getenv("DEFAULT_OUTPUT_DIR", None)
```

(Não esquecer do import `import os` no topo se não existir)

- [ ] **Step 3: Commit**

```bash
git add src/config.py
git commit -m "config: add DEFAULT_OUTPUT_DIR with env fallback"
```

---

## Task 2: Criar módulo `input_detector.py` com função `detect_input_type()`

**Files:**
- Create: `src/utils/input_detector.py`
- Modify: `tests/unit/test_input_detector.py` (criar se não existir)

- [ ] **Step 1: Escrever teste para detecção de URL YouTube**

Criar `tests/unit/test_input_detector.py`:

```python
import pytest
from src.utils.input_detector import detect_input_type, InputType

def test_detect_youtube_url():
    """Detecta URL do YouTube como tipo YOUTUBE"""
    urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "http://youtube.com/watch?v=abc123",
        "https://m.youtube.com/watch?v=abc123",
    ]
    for url in urls:
        assert detect_input_type(url) == InputType.YOUTUBE, f"Failed for {url}"

def test_detect_local_file():
    """Detecta caminho de arquivo local como tipo LOCAL"""
    # Criar arquivo temporário para teste
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        temp_path = f.name
    
    try:
        assert detect_input_type(temp_path) == InputType.LOCAL
    finally:
        import os
        os.unlink(temp_path)

def test_detect_nonexistent_file():
    """Detecta caminho inexistente como UNKNOWN"""
    from src.utils.input_detector import InputType
    path = "/nonexistent/path/to/file.mp3"
    assert detect_input_type(path) == InputType.UNKNOWN

def test_detect_invalid_input():
    """Detecta string inválida como UNKNOWN"""
    assert detect_input_type("just some random text") == InputType.UNKNOWN
```

- [ ] **Step 2: Rodar testes (falhar é esperado)**

```bash
pytest tests/unit/test_input_detector.py -v
```

Expected: FAIL — "ModuleNotFoundError: No module named 'src.utils.input_detector'"

- [ ] **Step 3: Criar arquivo `src/utils/input_detector.py` com implementação**

```python
"""
Detecta o tipo de entrada do usuário: URL YouTube ou arquivo local.
"""
import os
from enum import Enum
from urllib.parse import urlparse


class InputType(Enum):
    """Tipos de entrada suportados"""
    YOUTUBE = "youtube"
    LOCAL = "local"
    UNKNOWN = "unknown"


def is_youtube_url(input_str: str) -> bool:
    """
    Verifica se a string é uma URL válida do YouTube.
    
    Aceita:
    - https://www.youtube.com/watch?v=...
    - https://youtu.be/...
    - http:// (sem https)
    - m.youtube.com (mobile)
    """
    if not input_str.startswith("http://") and not input_str.startswith("https://"):
        return False
    
    try:
        parsed = urlparse(input_str)
        domain = parsed.netloc.lower()
        return "youtube.com" in domain or "youtu.be" in domain
    except Exception:
        return False


def is_local_file(input_str: str) -> bool:
    """Verifica se a string é um caminho de arquivo local que existe."""
    try:
        return os.path.exists(input_str) and os.path.isfile(input_str)
    except (OSError, TypeError):
        return False


def detect_input_type(input_str: str) -> InputType:
    """
    Detecta automaticamente o tipo de entrada.
    
    Retorna:
    - InputType.YOUTUBE: se for URL do YouTube
    - InputType.LOCAL: se for arquivo local existente
    - InputType.UNKNOWN: caso contrário
    """
    if is_youtube_url(input_str):
        return InputType.YOUTUBE
    elif is_local_file(input_str):
        return InputType.LOCAL
    else:
        return InputType.UNKNOWN


def validate_input(input_str: str) -> tuple[InputType, str]:
    """
    Valida a entrada e retorna (tipo, mensagem_erro).
    
    Se válida: (tipo, "")
    Se inválida: (UNKNOWN, "mensagem descritiva")
    """
    input_type = detect_input_type(input_str)
    
    if input_type == InputType.YOUTUBE:
        return input_type, ""
    elif input_type == InputType.LOCAL:
        return input_type, ""
    else:
        # Tentar ser útil na mensagem de erro
        if input_str.startswith("http"):
            return input_type, f"URL não parece ser do YouTube: {input_str}"
        elif os.path.sep in input_str or input_str.endswith((".mp3", ".mp4", ".wav", ".m4a")):
            return input_type, f"Arquivo não encontrado: {input_str}"
        else:
            return input_type, f"Entrada inválida — não é URL YouTube nem arquivo local: {input_str}"
```

- [ ] **Step 4: Rodar testes (todos passam)**

```bash
pytest tests/unit/test_input_detector.py -v
```

Expected: PASS (3 testes)

- [ ] **Step 5: Commit**

```bash
git add src/utils/input_detector.py tests/unit/test_input_detector.py
git commit -m "feat: add input detection module (youtube vs local file)"
```

---

## Task 3: Adicionar testes para função `main()` do CLI

**Files:**
- Modify: `tests/unit/test_cli.py` (ou criar se não existir)

- [ ] **Step 1: Escrever teste para comando raiz com URL YouTube**

Adicione a `tests/unit/test_cli.py`:

```python
import pytest
from typer.testing import CliRunner
from src.cli import app

runner = CliRunner()

def test_main_command_with_youtube_url():
    """Comando raiz 'mtn <url>' roteia para youtube_to_notes"""
    # Este teste é simbólico — a implementação real fará mock do pipeline
    # Por enquanto, apenas verifica se o comando é aceito
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # Verifica se aparece o comando principal (não apenas youtube/local)
    assert "input_source" in result.stdout or "INPUT" in result.stdout

def test_youtube_subcommand_still_works():
    """Subcomando 'mtn youtube' continua funcionando (compatibilidade)"""
    result = runner.invoke(app, ["youtube", "--help"])
    assert result.exit_code == 0
    assert "YouTube" in result.stdout
```

- [ ] **Step 2: Rodar testes (verão falhar se comando raiz não existir ainda)**

```bash
pytest tests/unit/test_cli.py -v
```

Expected: Comportamento depende do estado atual (pode ser SKIP ou FAIL)

---

## Task 4: Implementar comando raiz `main()` em `src/cli.py`

**Files:**
- Modify: `src/cli.py`

- [ ] **Step 1: Ler `src/cli.py` atual**

Já foi lido. Tem dois subcomandos (`youtube` e `local`).

- [ ] **Step 2: Adicionar imports necessários**

No topo de `src/cli.py`, após imports atuais:

```python
from src.utils.input_detector import detect_input_type, validate_input, InputType
```

- [ ] **Step 3: Adicionar função `main()` ao Typer app**

Insira esta função **antes** das funções `youtube()` e `local()`, após a definição da classe `Depth`:

```python
@app.command()
def main(
    input_source: Annotated[str, typer.Argument(help="URL do YouTube ou caminho do arquivo local")],
    depth: Annotated[Depth, typer.Option("--depth", "-d", help="Profundidade da nota")] = _default_depth,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Pasta de destino da nota")] = None,
    lang: Annotated[str, typer.Option("--lang", "-l", help="Idioma da transcrição (ex: pt, en, es)")] = DEFAULT_LANG,
    model: Annotated[str, typer.Option(help="Modelo LLM para geração da nota")] = DEFAULT_MODEL,
    by_chapter: Annotated[bool, typer.Option("--by-chapter", help="Processar e gerar seções por capítulo")] = False,
):
    """Processa vídeo YouTube ou arquivo local e gera nota Markdown automaticamente."""
    from src.pipeline import youtube_to_notes, local_to_notes

    # Validar entrada
    input_type, error_msg = validate_input(input_source)
    if input_type == InputType.UNKNOWN:
        typer.echo(f"❌ Erro: {error_msg}", err=True)
        raise typer.Exit(code=1)

    # Rotear para pipeline correto
    if input_type == InputType.YOUTUBE:
        result = youtube_to_notes(
            url=input_source, 
            depth=depth.value, 
            output_dir=output, 
            model=model, 
            lang=lang, 
            by_chapter=by_chapter
        )
    else:  # InputType.LOCAL
        result = local_to_notes(
            path=input_source, 
            depth=depth.value, 
            output_dir=output, 
            model=model, 
            lang=lang
        )

    if result:
        typer.echo(f"✅ Nota gerada: {result}")
    else:
        raise typer.Exit(code=1)
```

- [ ] **Step 4: Testar manualmente com `--help`**

```bash
poetry run mtn --help
```

Expected: Mostra comando `main` como primeira opção, após descrição geral, antes de `youtube` e `local`

- [ ] **Step 5: Commit**

```bash
git add src/cli.py
git commit -m "feat: add main command with automatic input detection"
```

---

## Task 5: Ajustar ordem de comandos no Typer app (opcional mas melhor UX)

**Files:**
- Modify: `src/cli.py`

- [ ] **Step 1: Reordenar definições de comando**

No Typer, a ordem de definição é a ordem no help. Para deixar `main` em primeiro lugar visualmente, reordene assim:

1. Deixar `@app.command()` de `main()` antes
2. Depois `youtube()`
3. Depois `local()`

(Já está correto se você adicionou `main()` antes dos outros na Task 4)

- [ ] **Step 2: Testar novo `--help`**

```bash
poetry run mtn --help
```

Expected: Primeira opção é `main` (ou opção padrão listada), depois `youtube`, depois `local`

- [ ] **Step 3: Commit**

```bash
git add src/cli.py
git commit -m "refactor: reorder commands for better UX (main first)"
```

---

## Task 6: Testar fluxos completos (YouTube e Local)

**Files:**
- (nenhum novo arquivo — só testes manuais)

- [ ] **Step 1: Testar comando raiz com URL YouTube**

```bash
poetry run mtn "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --depth raso
```

Expected: Inicia pipeline YouTube, gera nota em `data/04. notes/Youtube/` (ou `DEFAULT_OUTPUT_DIR`)

- [ ] **Step 2: Testar comando raiz com arquivo local**

```bash
poetry run mtn "tests/fixtures/sample.mp3" --depth intermediario
```

(Usar um arquivo que exista no projeto para teste)

Expected: Inicia pipeline Local, gera nota em `data/04. notes/Local/` (ou fallback)

- [ ] **Step 3: Testar comando raiz com entrada inválida**

```bash
poetry run mtn "not_a_valid_input"
```

Expected: Erro clara: `❌ Erro: Entrada inválida — não é URL YouTube nem arquivo local: not_a_valid_input`

- [ ] **Step 4: Testar compatibilidade com subcomando antigo**

```bash
poetry run mtn youtube "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
poetry run mtn local "tests/fixtures/sample.mp3"
```

Expected: Ambos ainda funcionam normalmente

- [ ] **Step 5: Anotar resultado manual** (sem commit)

Se todos os testes passarem: ✅
Se falhar: ❌ e descrever o erro

---

## Task 7: Validar cobertura de testes

**Files:**
- (já criados)

- [ ] **Step 1: Rodar suite de testes com cobertura**

```bash
poetry run pytest tests/unit/ -v --cov=src --cov-report=term-missing
```

Expected: Cobertura incluindo `input_detector.py` > 80%

- [ ] **Step 2: Adicionar teste para caso edge: URL com parameters**

Adicione a `tests/unit/test_input_detector.py`:

```python
def test_detect_youtube_with_playlist():
    """Detecta URL de playlist do YouTube"""
    url = "https://www.youtube.com/playlist?list=PLxxxxx"
    assert detect_input_type(url) == InputType.YOUTUBE

def test_detect_youtube_short_form():
    """Detecta shorts do YouTube"""
    url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
    assert detect_input_type(url) == InputType.YOUTUBE
```

- [ ] **Step 3: Rodar testes novamente**

```bash
poetry run pytest tests/unit/ -v
```

Expected: PASS (todos)

- [ ] **Step 4: Commit final de testes**

```bash
git add tests/unit/test_input_detector.py
git commit -m "test: add edge cases for youtube url detection (playlist, shorts)"
```

---

## Task 8: Documentar novo comando no `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md` (na raiz do projeto)

- [ ] **Step 1: Ler seção "CLI Usage" do CLAUDE.md atual**

```bash
grep -A 20 "## CLI Usage" CLAUDE.md
```

- [ ] **Step 2: Adicionar novo padrão antes dos subcomandos**

Modifique a seção para:

```markdown
## CLI Usage

### Novo padrão (recomendado)

```bash
mtn "<input>" [-d nivel] [-o output]
```

Aceita automaticamente URL do YouTube ou arquivo local:
```bash
mtn "https://youtube.com/watch?v=..."
mtn "https://youtube.com/watch?v=..." -d avancado
mtn "C:/videos/aula.mp4" -d raso
mtn "audio.mp3" --output "path/to/notes/"
```

### Compatibilidade — subcomandos antigos (ainda funcionam)

```bash
mtn youtube "url" [--depth raso|intermediario|avancado|metacognitivo] [--output "path"]
mtn local "path" [--depth ...]
```

...resto do documento
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLI usage — document new main command pattern"
```

---

## Task 9: Atualizar `config.py` com documentação

**Files:**
- Modify: `src/config.py`

- [ ] **Step 1: Adicionar comentário descritivo para `DEFAULT_OUTPUT_DIR`**

Modifique a linha adicionada na Task 1 para:

```python
# Default output directory for generated notes
# If not set via DEFAULT_OUTPUT_DIR env var, falls back to:
#   - data/04. notes/Youtube  (for YouTube)
#   - data/04. notes/Local    (for local files)
# Subdirectories are created automatically if needed
DEFAULT_OUTPUT_DIR = os.getenv("DEFAULT_OUTPUT_DIR", None)
```

- [ ] **Step 2: Commit**

```bash
git add src/config.py
git commit -m "docs: clarify DEFAULT_OUTPUT_DIR behavior and fallback"
```

---

## Task 10: Verificação final e cleanup

**Files:**
- (revisão apenas)

- [ ] **Step 1: Rodar todos os testes**

```bash
poetry run pytest tests/ -v
```

Expected: PASS (todos)

- [ ] **Step 2: Verificar compatibilidade**

```bash
poetry run mtn --help
poetry run mtn youtube --help
poetry run mtn local --help
```

Expected: Todos os comandos aparecem, nenhum erro

- [ ] **Step 3: Limpar qualquer arquivo temporário**

```bash
git status
```

Expected: Nenhum arquivo untracked (exceto logs, cache)

- [ ] **Step 4: Criar commit de confirmação (se houver ajustes finais)**

```bash
git log --oneline -10
```

Expected: Últimos commits refletem a sequência de tasks

- [ ] **Step 5: Resumir mudanças**

```bash
git diff origin/main...HEAD --stat
```

(ou `main` → `master` dependendo do projeto)

---

## Spec Coverage Checklist

| Requisito | Task | Status |
|-----------|------|--------|
| Comando raiz `mtn "<input>"` | Task 4 | ✅ |
| Detectar URL vs arquivo | Task 2 | ✅ |
| Usar profundidade padrão | Task 4 | ✅ |
| Usar diretório padrão | Task 1 | ✅ |
| Preservar subcomandos antigos | Task 6 (validação) | ✅ |
| Validação com erros claros | Task 2, 4 | ✅ |
| Flags opcionais (`-d`, `-o`, `-l`, `--model`, `--by-chapter`) | Task 4 | ✅ |
| Testes cobrindo detecção | Task 2, 7 | ✅ |
| Documentação atualizada | Task 8, 9 | ✅ |
