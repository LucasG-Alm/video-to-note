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
from src.core.notes2 import gerar_nota_md
from src.utils.utils import print_hex_color

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


def youtube_to_notes(
    url: str,
    depth: str = "intermediario",
    output_dir: str = None,
    model: str = "llama-3.3-70b-versatile",
    pasta_destino: str = "",
    delay: bool = False,
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

    # Tenta legenda primeiro, cai no Whisper se não tiver
    transcript = get_transcript_with_yt_dlp(url)
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
        final_transcript = transcrever_audio_inteligente(audio_path)
        metadata['transcription_by'] = 'Groq Whisper API'

    json_path = PROJECT_ROOT / "data/03. transcriptions/Youtube" / pasta_destino / f"{title}.json"
    salvar_transcricao(metadata, final_transcript, str(json_path))

    try:
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
    depth: str = "intermediario",
    output_dir: str = None,
    model: str = "llama-3.3-70b-versatile",
):
    """Pipeline: arquivo local de áudio/vídeo → transcrição → nota Markdown."""
    audio_path = Path(path)
    if not audio_path.exists():
        print_hex_color('#f92f60', "❌ Arquivo não encontrado:", str(audio_path))
        return None

    title = audio_path.stem
    print_hex_color('#32cbff', "🎵 Processando arquivo local:", title)

    transcription = transcrever_audio_inteligente(str(audio_path))

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
