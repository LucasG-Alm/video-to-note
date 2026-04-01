"""Testes para CLI do Media to Notes"""
import pytest
from typer.testing import CliRunner
from src.cli import app

runner = CliRunner()


class TestMainCommand:
    """Testes para o comando principal (raiz)"""

    def test_main_help(self):
        """Comando --help mostra disponibilidade de comandos"""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        # Verificar que mostra os comandos disponíveis
        assert "Usage:" in result.stdout

    def test_main_no_args_shows_usage(self):
        """Rodar sem argumentos mostra help/usage (com erro, exit_code=2)"""
        result = runner.invoke(app, [])
        # Com subcomandos, Typer retorna exit_code=2 (erro) se nenhum comando é fornecido
        assert result.exit_code == 2
        # Mas mostra a mensagem de usage
        assert "Usage:" in result.stdout or "Commands:" in result.stdout


class TestYoutubeSubcommand:
    """Testes para subcomando youtube (compatibilidade)"""

    def test_youtube_help(self):
        """Subcomando youtube mostra help"""
        result = runner.invoke(app, ["youtube", "--help"])
        assert result.exit_code == 0
        assert "YouTube" in result.stdout or "youtube" in result.stdout.lower()

    def test_youtube_no_url_error(self):
        """Subcomando youtube sem URL retorna erro"""
        result = runner.invoke(app, ["youtube"])
        # Typer retorna erro quando falta argumento obrigatório
        assert result.exit_code != 0


class TestLocalSubcommand:
    """Testes para subcomando local (compatibilidade)"""

    def test_local_help(self):
        """Subcomando local mostra help"""
        result = runner.invoke(app, ["local", "--help"])
        assert result.exit_code == 0
        assert "local" in result.stdout.lower() or "arquivo" in result.stdout.lower()

    def test_local_no_path_error(self):
        """Subcomando local sem path retorna erro"""
        result = runner.invoke(app, ["local"])
        # Typer retorna erro quando falta argumento obrigatório
        assert result.exit_code != 0


class TestConfigCommand:
    """Testes para comando config"""

    def test_config_help(self):
        """Comando config mostra help"""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "config" in result.stdout.lower()

    def test_config_show(self):
        """Comando config --show mostra configuração atual"""
        result = runner.invoke(app, ["config", "--show"])
        assert result.exit_code == 0
        assert "DEFAULT_OUTPUT_DIR" in result.stdout
