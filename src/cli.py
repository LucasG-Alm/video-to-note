import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from enum import Enum
from typing import Optional
from pathlib import Path

import typer
from typing import Annotated

from src.config import DEFAULT_MODEL, DEFAULT_DEPTH, DEFAULT_LANG, DEFAULT_OUTPUT_DIR, save_config_to_env

app = typer.Typer(
    name="mtn",
    help="Media to Notes — converte vídeos e áudios em notas Markdown.",
    no_args_is_help=True,
)


class Depth(str, Enum):
    raso = "raso"
    intermediario = "intermediario"
    avancado = "avancado"
    metacognitivo = "metacognitivo"


_default_depth = Depth(DEFAULT_DEPTH)


@app.command()
def config(
    set_output_dir: Annotated[Optional[str], typer.Option("--set-output", help="Define o diretório de saída padrão")] = None,
    show: Annotated[bool, typer.Option("--show", help="Mostra configuração atual")] = False,
):
    """Gerencia configurações do MTN (DEFAULT_OUTPUT_DIR, etc)."""
    if show:
        current = DEFAULT_OUTPUT_DIR or "data/04. notes/ (padrão)"
        typer.echo(f"📋 Configuração atual:")
        typer.echo(f"   DEFAULT_OUTPUT_DIR = {current}")
        return

    if set_output_dir:
        path = Path(set_output_dir)
        path.mkdir(parents=True, exist_ok=True)
        save_config_to_env("DEFAULT_OUTPUT_DIR", str(path.absolute()))
        typer.echo(f"✅ Diretório de saída salvo em .env: {path.absolute()}")
        return

    # Se nenhuma opção foi fornecida, mostra help
    typer.echo("Use: mtn config --set-output <caminho>  ou  mtn config --show")


@app.command()
def youtube(
    url: Annotated[str, typer.Argument(help="URL do vídeo no YouTube")],
    depth: Annotated[Depth, typer.Option("--depth", "-d", help="Profundidade da nota")] = _default_depth,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Pasta de destino da nota")] = None,
    lang: Annotated[str, typer.Option("--lang", "-l", help="Idioma da transcrição (ex: pt, en, es)")] = DEFAULT_LANG,
    model: Annotated[str, typer.Option(help="Modelo LLM para geração da nota")] = DEFAULT_MODEL,
    by_chapter: Annotated[bool, typer.Option("--by-chapter", help="Processar e gerar seções por capítulo")] = False,
):
    """Processa um vídeo do YouTube e gera uma nota Markdown."""
    from src.pipeline import youtube_to_notes

    result = youtube_to_notes(url=url, depth=depth.value, output_dir=output, model=model, lang=lang, by_chapter=by_chapter)
    if result:
        typer.echo(f"✅ Nota gerada: {result}")
    else:
        raise typer.Exit(code=1)


@app.command()
def local(
    path: Annotated[str, typer.Argument(help="Caminho para o arquivo de áudio ou vídeo")],
    depth: Annotated[Depth, typer.Option("--depth", "-d", help="Profundidade da nota")] = _default_depth,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Pasta de destino da nota")] = None,
    lang: Annotated[str, typer.Option("--lang", "-l", help="Idioma da transcrição (ex: pt, en, es)")] = DEFAULT_LANG,
    model: Annotated[str, typer.Option(help="Modelo LLM para geração da nota")] = DEFAULT_MODEL,
):
    """Processa um arquivo local de áudio ou vídeo e gera uma nota Markdown."""
    from src.pipeline import local_to_notes

    result = local_to_notes(path=path, depth=depth.value, output_dir=output, model=model, lang=lang)
    if result:
        typer.echo(f"✅ Nota gerada: {result}")
    else:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
