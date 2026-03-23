import time
import random
from pathlib import Path
from datetime import datetime

from src.services.youtube import (
    extract_video_id, get_video_metadata, sanitize_filename,
    get_transcript_with_yt_dlp, transcript_to_text,
    download_audio_from_youtube,
)
from src.services.transcription import transcrever_audio_inteligente, salvar_transcricao
from src.core.notes2 import gerar_nota_md, split_transcript_by_chapters, _invoke_llm_with_fallback, FALLBACK_MODEL
from src.utils.utils import print_hex_color
from src.config import DEFAULT_MODEL, DEFAULT_DEPTH, DEFAULT_LANG

PROJECT_ROOT = Path(__file__).parent.parent

DEPTH_TEMPLATES = {
    "raso": "template_youtube_raso.md",
    "intermediario": "template_youtube_intermediario.md",
    "avancado": "template_youtube_avancado.md",
    "metacognitivo": "template_youtube_metacognitivo.md",
}


def resolve_template(depth: str) -> str:
    filename = DEPTH_TEMPLATES.get(depth, "template_youtube_intermediario.md")
    path = PROJECT_ROOT / "templates" / filename
    if not path.exists():
        raise FileNotFoundError(f"Template não encontrado: {path}")
    return str(path)


def _gerar_nota_por_capitulos(
    json_path: str,
    segments: list,
    chapters: list,
    template_path: str,
    title: str,
    model: str,
    output_dir: str = None,
) -> Path:
    """Gera nota com seções ## por capítulo, processando cada um via LLM."""
    import os
    from dotenv import load_dotenv
    from langchain.prompts import ChatPromptTemplate

    load_dotenv(PROJECT_ROOT / '.env')
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY não encontrada.")

    grupos = split_transcript_by_chapters(segments, chapters)
    print_hex_color('#32cbff', f"📚 Processando {len(grupos)} capítulos...", "")

    secoes = []
    for i, grupo in enumerate(grupos, 1):
        chapter_title = grupo['title'] or f"Parte {i}"
        print_hex_color('#32cbff', f"  [{i}/{len(grupos)}] {chapter_title}", "")
        if not grupo['text'].strip():
            secoes.append(f"## {chapter_title}\n\n*(sem transcrição disponível)*")
            continue
        prompt = f"Resuma os pontos principais deste trecho do vídeo em tópicos concisos:\n\n{grupo['text']}"
        conteudo = _invoke_llm_with_fallback(
            prompt_text=prompt,
            primary_model=model,
            fallback_model=FALLBACK_MODEL,
            api_key=api_key,
        )
        secoes.append(f"## {chapter_title}\n\n{conteudo}")

    nota_final = f"# {title}\n\n" + "\n\n---\n\n".join(secoes)

    if output_dir:
        pasta_saida = Path(output_dir)
    else:
        pasta_saida = PROJECT_ROOT / "data/04. notes/Youtube"
    pasta_saida.mkdir(parents=True, exist_ok=True)

    path_saida = pasta_saida / f"{title}.md"
    with open(path_saida, 'w', encoding='utf-8') as f:
        f.write(nota_final)

    print_hex_color('#0bd271', "✅ Nota por capítulos salva em:", str(path_saida))
    return path_saida


def youtube_to_notes(
    url: str,
    depth: str = DEFAULT_DEPTH,
    output_dir: str = None,
    model: str = DEFAULT_MODEL,
    lang: str = DEFAULT_LANG,
    pasta_destino: str = "",
    delay: bool = False,
    by_chapter: bool = False,
):
    """Pipeline completo: YouTube URL → transcrição → nota Markdown."""
    video_id = extract_video_id(url)
    if not video_id:
        print_hex_color('#f92f60', "❌ Não foi possível extrair o ID do vídeo.", f"URL: {url}")
        return None

    metadata = get_video_metadata(url)
    if not metadata:
        print_hex_color('#f92f60', "❌ Falha ao obter metadados.", "")
        return None

    title = sanitize_filename(metadata['title'])
    print_hex_color('#32cbff', "🎬 Processando:", title)

    json_path = PROJECT_ROOT / "data/03. transcriptions/Youtube" / pasta_destino / f"{title}.json"

    # Reutiliza transcrição existente se o JSON já estiver em disco
    if json_path.exists():
        import json as _json
        print_hex_color('#32cbff', "♻️  Transcrição em cache, pulando download.", "")
        with open(json_path, encoding='utf-8') as f:
            cached = _json.load(f)
        final_transcript = cached.get('transcription', {})
        metadata = {**cached.get('metadata', metadata), **{k: v for k, v in metadata.items() if k not in cached.get('metadata', {})}}
    else:
        # Tenta legenda primeiro, cai no Whisper se não tiver
        transcript = get_transcript_with_yt_dlp(url, lang=lang)
        if transcript:
            final_transcript = {
                'text': transcript_to_text(transcript),
                'segments': transcript,
            }
        else:
            print_hex_color('#f92f60', "❌ Sem legenda disponível, tentando Whisper...")
            print_hex_color("#ffaa00", "⚠️  Baixando áudio para transcrição com Whisper...")
            audio_dir = str(PROJECT_ROOT / "data/02. audio/Youtube" / pasta_destino)
            audio_path = download_audio_from_youtube(url, audio_dir)
            if not audio_path:
                print_hex_color('#f92f60', "❌ Não foi possível baixar o áudio.", "")
                return None
            final_transcript = transcrever_audio_inteligente(audio_path, idioma=lang)
            metadata['transcription_by'] = 'Groq Whisper API'
        salvar_transcricao(metadata, final_transcript, str(json_path))

    try:
        if by_chapter and metadata.get('chapters'):
            output = _gerar_nota_por_capitulos(
                json_path=str(json_path),
                segments=final_transcript.get('segments', []),
                chapters=metadata['chapters'],
                template_path=resolve_template(depth),
                title=title,
                model=model,
                output_dir=output_dir,
            )
        else:
            output = gerar_nota_md(
                path_transcricao_json=str(json_path),
                path_template_md=resolve_template(depth),
                metadata={"tags_md": "YouTube/Vídeo"},
                model=model,
                output_dir=output_dir,
            )
    except Exception as e:
        print_hex_color('#f92f60', f"❌ Erro ao gerar nota: {e}", "")
        return None

    if delay:
        wait = random.uniform(90, 150)
        print(f"Aguardando {round(wait, 2)}s para não tomar bloco 🚫")
        time.sleep(wait)

    return output


def local_to_notes(
    path: str,
    depth: str = DEFAULT_DEPTH,
    output_dir: str = None,
    model: str = DEFAULT_MODEL,
    lang: str = DEFAULT_LANG,
):
    """Pipeline: arquivo local de áudio/vídeo → transcrição → nota Markdown."""
    audio_path = Path(path)
    if not audio_path.exists():
        print_hex_color('#f92f60', "❌ Arquivo não encontrado:", str(audio_path))
        return None

    title = audio_path.stem
    print_hex_color('#32cbff', "🎵 Processando arquivo local:", title)

    transcription = transcrever_audio_inteligente(str(audio_path), idioma=lang)

    metadata = {
        'title': title,
        'uploader': 'Local',
        'webpage_url': str(audio_path),
        'duration_sec': 0,
        'chapters': [],
        'transcription_by': 'Groq Whisper API',
        'date_generated': datetime.now().isoformat(),
        'api': 'local',
        'type_file': audio_path.suffix.lstrip('.'),
        'source': str(audio_path),
    }

    json_path = PROJECT_ROOT / "data/03. transcriptions/Local" / f"{title}.json"
    salvar_transcricao(metadata, transcription, str(json_path))

    try:
        output = gerar_nota_md(
            path_transcricao_json=str(json_path),
            path_template_md=resolve_template(depth),
            metadata={"tags_md": "Media/Local"},
            model=model,
            output_dir=output_dir,
        )
    except Exception as e:
        print_hex_color('#f92f60', f"❌ Erro ao gerar nota: {e}", "")
        return None

    return output
