import pytest
import tempfile
import os
from src.utils.input_detector import detect_input_type, validate_input, InputType


class TestYoutubeDetection:
    """Testes para detecção de URLs do YouTube"""

    def test_detect_youtube_standard_url(self):
        """Detecta URL padrão do YouTube"""
        assert detect_input_type("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == InputType.YOUTUBE

    def test_detect_youtube_short_url(self):
        """Detecta URL curta youtu.be"""
        assert detect_input_type("https://youtu.be/dQw4w9WgXcQ") == InputType.YOUTUBE

    def test_detect_youtube_http(self):
        """Detecta URL com http (não https)"""
        assert detect_input_type("http://youtube.com/watch?v=abc123") == InputType.YOUTUBE

    def test_detect_youtube_mobile(self):
        """Detecta URL móvel do YouTube"""
        assert detect_input_type("https://m.youtube.com/watch?v=abc123") == InputType.YOUTUBE

    def test_detect_youtube_with_playlist(self):
        """Detecta URL de playlist do YouTube"""
        assert detect_input_type("https://www.youtube.com/playlist?list=PLxxxxx") == InputType.YOUTUBE

    def test_detect_youtube_shorts(self):
        """Detecta YouTube Shorts"""
        assert detect_input_type("https://www.youtube.com/shorts/dQw4w9WgXcQ") == InputType.YOUTUBE


class TestLocalFileDetection:
    """Testes para detecção de arquivos locais"""

    def test_detect_local_file_exists(self):
        """Detecta arquivo local existente"""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name

        try:
            assert detect_input_type(temp_path) == InputType.LOCAL
        finally:
            os.unlink(temp_path)

    def test_detect_local_video_file(self):
        """Detecta arquivo de vídeo local"""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            temp_path = f.name

        try:
            assert detect_input_type(temp_path) == InputType.LOCAL
        finally:
            os.unlink(temp_path)


class TestUnknownInput:
    """Testes para entrada desconhecida"""

    def test_detect_nonexistent_file(self):
        """Detecta caminho inexistente como UNKNOWN"""
        assert detect_input_type("/nonexistent/path/to/file.mp3") == InputType.UNKNOWN

    def test_detect_invalid_text(self):
        """Detecta texto aleatório como UNKNOWN"""
        assert detect_input_type("just some random text") == InputType.UNKNOWN

    def test_detect_invalid_url(self):
        """Detecta URL que não é YouTube como UNKNOWN"""
        assert detect_input_type("https://www.google.com") == InputType.UNKNOWN


class TestValidation:
    """Testes para validação com mensagens de erro"""

    def test_validate_youtube_url(self):
        """Valida URL do YouTube retorna tipo e sem erro"""
        input_type, error = validate_input("https://www.youtube.com/watch?v=abc123")
        assert input_type == InputType.YOUTUBE
        assert error == ""

    def test_validate_local_file(self):
        """Valida arquivo local retorna tipo e sem erro"""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name

        try:
            input_type, error = validate_input(temp_path)
            assert input_type == InputType.LOCAL
            assert error == ""
        finally:
            os.unlink(temp_path)

    def test_validate_nonexistent_file(self):
        """Validação de arquivo inexistente retorna erro claro"""
        input_type, error = validate_input("/nonexistent/file.mp3")
        assert input_type == InputType.UNKNOWN
        assert "Arquivo não encontrado" in error

    def test_validate_invalid_http_url(self):
        """Validação de URL HTTP (não YouTube) retorna erro"""
        input_type, error = validate_input("https://www.google.com")
        assert input_type == InputType.UNKNOWN
        assert "não parece ser do YouTube" in error or "inválida" in error

    def test_validate_invalid_text(self):
        """Validação de texto aleatório retorna erro"""
        input_type, error = validate_input("some text")
        assert input_type == InputType.UNKNOWN
        assert "inválida" in error
