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
