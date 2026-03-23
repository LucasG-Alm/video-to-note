"""
Testes para src/cli.py

Usamos duas ferramentas novas aqui:

1. CliRunner (typer.testing)
   → Simula a execução do CLI sem abrir um terminal real.
     runner.invoke(app, ["youtube", "url"]) é equivalente a rodar
     `mtn youtube url` no shell, mas captura output e exit_code para
     que o teste possa inspecionar o resultado.

2. unittest.mock.patch
   → Substitui temporariamente uma função real por um Mock controlado.
     Assim testamos APENAS a lógica do CLI (parseamento de argumentos,
     chamada correta do pipeline, exit codes) sem executar o pipeline
     de verdade — sem rede, sem API, sem disco.

     patch("src.pipeline.youtube_to_notes") intercepta a função no
     módulo onde ela vive. Como o CLI faz `from src.pipeline import ...`
     dentro da função (lazy import), o patch precisa estar no módulo
     de origem, não no cli.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


class TestYoutubeCommand:
    """
    `mtn youtube <url>` deve:
    - Aceitar URL como argumento obrigatório
    - Rejeitar depth inválido
    - Passar os argumentos corretos para youtube_to_notes()
    - Sair com código 0 quando a nota é gerada com sucesso
    - Sair com código 1 quando o pipeline retorna None (falha)
    """

    def test_help_exibe_argumentos(self):
        result = runner.invoke(app, ["youtube", "--help"])
        assert result.exit_code == 0
        assert "url" in result.output.lower()
        assert "depth" in result.output.lower()

    def test_depth_invalido_retorna_erro(self):
        # Typer valida o Enum automaticamente — não deve chegar no pipeline
        result = runner.invoke(app, ["youtube", "https://youtu.be/abc", "--depth", "ultra_profundo"])
        assert result.exit_code != 0

    def test_chama_pipeline_com_defaults(self):
        # Sem --depth, --lang e --output: deve usar valores do config
        with patch("src.pipeline.youtube_to_notes", return_value=Path("nota.md")) as mock:
            result = runner.invoke(app, ["youtube", "https://youtu.be/XswU6CRs79s"])

        mock.assert_called_once_with(
            url="https://youtu.be/XswU6CRs79s",
            depth="intermediario",
            output_dir=None,
            model="llama-3.3-70b-versatile",
            lang="pt",
        )
        assert result.exit_code == 0

    def test_depth_avancado_e_repassado_ao_pipeline(self):
        with patch("src.pipeline.youtube_to_notes", return_value=Path("nota.md")) as mock:
            runner.invoke(app, ["youtube", "https://youtu.be/abc", "--depth", "avancado"])

        assert mock.call_args.kwargs["depth"] == "avancado"

    def test_output_e_repassado_ao_pipeline(self):
        with patch("src.pipeline.youtube_to_notes", return_value=Path("nota.md")) as mock:
            runner.invoke(app, ["youtube", "url", "--output", "C:/vault/_revisar/"])

        assert mock.call_args.kwargs["output_dir"] == "C:/vault/_revisar/"

    def test_lang_en_e_repassado_ao_pipeline(self):
        with patch("src.pipeline.youtube_to_notes", return_value=Path("nota.md")) as mock:
            runner.invoke(app, ["youtube", "url", "--lang", "en"])

        assert mock.call_args.kwargs["lang"] == "en"

    def test_exit_0_quando_nota_gerada(self):
        with patch("src.pipeline.youtube_to_notes", return_value=Path("nota.md")):
            result = runner.invoke(app, ["youtube", "https://youtu.be/abc"])
        assert result.exit_code == 0

    def test_exit_1_quando_pipeline_retorna_none(self):
        # Pipeline retorna None quando algo deu errado (sem ID, sem áudio, etc.)
        # O CLI deve propagar a falha com exit code 1
        with patch("src.pipeline.youtube_to_notes", return_value=None):
            result = runner.invoke(app, ["youtube", "https://youtu.be/abc"])
        assert result.exit_code == 1


class TestLocalCommand:
    """
    `mtn local <path>` deve:
    - Aceitar caminho de arquivo como argumento obrigatório
    - Passar os argumentos corretos para local_to_notes()
    - Sair com código 0 quando a nota é gerada com sucesso
    - Sair com código 1 quando o pipeline retorna None
    """

    def test_help_exibe_argumentos(self):
        result = runner.invoke(app, ["local", "--help"])
        assert result.exit_code == 0
        assert "path" in result.output.lower()

    def test_chama_pipeline_com_defaults(self):
        with patch("src.pipeline.local_to_notes", return_value=Path("nota.md")) as mock:
            result = runner.invoke(app, ["local", "audio.mp3"])

        mock.assert_called_once_with(
            path="audio.mp3",
            depth="intermediario",
            output_dir=None,
            model="llama-3.3-70b-versatile",
            lang="pt",
        )
        assert result.exit_code == 0

    def test_depth_metacognitivo_e_repassado(self):
        with patch("src.pipeline.local_to_notes", return_value=Path("nota.md")) as mock:
            runner.invoke(app, ["local", "audio.mp3", "--depth", "metacognitivo"])

        assert mock.call_args.kwargs["depth"] == "metacognitivo"

    def test_exit_1_quando_pipeline_retorna_none(self):
        with patch("src.pipeline.local_to_notes", return_value=None):
            result = runner.invoke(app, ["local", "audio.mp3"])
        assert result.exit_code == 1


class TestAppGeral:
    """Comportamento do app como um todo."""

    def test_sem_argumentos_exibe_help(self):
        # no_args_is_help=True no Typer retorna exit code 2 (padrão de "missing args")
        # O que importa é que os subcomandos estejam listados no output
        result = runner.invoke(app, [])
        assert "youtube" in result.output.lower()
        assert "local" in result.output.lower()

    def test_stdout_encoding_utf8(self):
        """
        ERR-01 — cli.py deve reconfigurar stdout para UTF-8 ao ser importado.

        No Windows, o terminal padrão usa cp1252, que não suporta emojis.
        sys.stdout.reconfigure(encoding='utf-8') garante que os emojis do
        pipeline (✅ 🎬 ⚠️) não estourem UnicodeEncodeError.

        Importar src.cli já executa o reconfigure (nível de módulo).
        """
        import sys
        import src.cli  # noqa: F401 — side effect intencional
        assert sys.stdout.encoding.lower() == "utf-8"
