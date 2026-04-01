"""
Detecta o tipo de entrada do usuário: URL YouTube ou arquivo local.
"""
import os
import re
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
    - youtube.com/shorts/...
    - youtube.com/playlist?list=...
    """
    if not input_str.startswith("http://") and not input_str.startswith("https://"):
        return False

    try:
        parsed = urlparse(input_str)
        domain = parsed.netloc.lower()

        # Verificar domínios YouTube válidos
        if "youtube.com" in domain or "youtu.be" in domain:
            return True

        return False
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
        elif os.path.sep in input_str or input_str.endswith(
            (".mp3", ".mp4", ".wav", ".m4a", ".aac", ".flac")
        ):
            return input_type, f"Arquivo não encontrado: {input_str}"
        else:
            return (
                input_type,
                f"Entrada inválida — não é URL YouTube nem arquivo local: {input_str}",
            )
