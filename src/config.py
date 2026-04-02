import os
import tomllib
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent
_config_path = _PROJECT_ROOT / "config.toml"

try:
    with open(_config_path, "rb") as _f:
        _cfg = tomllib.load(_f)
except FileNotFoundError:
    raise FileNotFoundError(
        f"config.toml não encontrado em {_config_path}. "
        "Copie config.toml.example para config.toml e ajuste os valores."
    )

DEFAULT_MODEL: str = _cfg["llm"]["model"]
DEFAULT_DEPTH: str = _cfg["pipeline"]["default_depth"]
DEFAULT_LANG: str = _cfg["pipeline"]["default_lang"]
COOKIES_FROM_BROWSER: str = _cfg["youtube"]["cookies_from_browser"]

# Default output directory for generated notes
# If not set via DEFAULT_OUTPUT_DIR env var, falls back to:
#   - data/04. notes/Youtube  (for YouTube)
#   - data/04. notes/Local    (for local files)
# Subdirectories are created automatically if needed
from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")
DEFAULT_OUTPUT_DIR = os.getenv("DEFAULT_OUTPUT_DIR", None)


def get_config() -> dict:
    """
    Carrega configuração do .env e retorna como dicionário.
    Retorna dict vazio se .env não existir.
    """
    env_path = _PROJECT_ROOT / ".env"
    config = {}

    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip()

    return config


def save_config_to_env(key: str, value: str) -> None:
    """
    Salva uma chave-valor no arquivo .env do projeto.
    Cria o arquivo se não existir.
    """
    env_path = _PROJECT_ROOT / ".env"
    lines = []
    key_found = False

    # Ler linhas existentes
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Garantir que termina com newline antes de processar
            if content and not content.endswith("\n"):
                content += "\n"
            lines = content.splitlines(keepends=True)

    # Atualizar ou adicionar a chave
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            key_found = True
        else:
            # Garantir que a linha termina com newline
            if line.strip():  # Ignorar linhas vazias
                if not line.endswith("\n"):
                    line = line + "\n"
            new_lines.append(line)

    if not key_found:
        new_lines.append(f"{key}={value}\n")

    # Escrever de volta
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
