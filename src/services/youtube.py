import re
import requests
from pathlib import Path
from yt_dlp import YoutubeDL
from datetime import datetime
import unicodedata

from src.services.transcription import transcrever_audio, transcrever_audio_inteligente, salvar_transcricao
from src.utils.utils import print_hex_color
from src.config import COOKIES_FROM_BROWSER

def extract_video_id(url):
    """Extrai o ID do vídeo do link do YouTube (watch, youtu.be e Shorts)."""
    match = re.search(r"(?:v=|youtu\.be/|shorts/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

def _vtt_time_to_seconds(time_str: str) -> float:
    """Converte timestamp VTT ('HH:MM:SS.mmm' ou 'MM:SS.mmm') para segundos."""
    parts = time_str.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    m, s = parts
    return int(m) * 60 + float(s)


def _parse_vtt(vtt_content: str) -> list:
    """
    Parseia conteúdo VTT e retorna segmentos com timestamps reais.
    Filtra entradas duplicadas que o YouTube gera para animação de karaokê.
    """
    cue_pattern = re.compile(
        r'(\d{1,2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3})'
        r'\s+-->\s+'
        r'(\d{1,2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3})'
        r'[^\n]*\n(.*?)(?=\n\n|\Z)',
        re.DOTALL,
    )
    segments = []
    seen_texts = set()
    for match in cue_pattern.finditer(vtt_content):
        start_str, end_str, raw_text = match.group(1), match.group(2), match.group(3)
        text = re.sub(r'<[^>]+>', '', raw_text).strip()  # remove tags <c>, <00:00:01.000>
        if not text or text in seen_texts:
            continue
        seen_texts.add(text)
        start = _vtt_time_to_seconds(start_str)
        end = _vtt_time_to_seconds(end_str)
        segments.append({'start': start, 'duration': end - start, 'text': text})
    return segments


def _parse_json3(data: dict) -> list:
    """Parseia formato json3 do YouTube. Timestamps podem ser 0 em legendas automáticas."""
    transcript = []
    for event in data.get('events', []):
        text = ''.join(seg.get('utf8', '') for seg in event.get('segs', []))
        if text.strip():
            transcript.append({
                'start': event.get('tStartMs', event.get('t', 0)) / 1000,
                'duration': event.get('dDurationMs', event.get('d', 0)) / 1000,
                'text': text.strip(),
            })
    return transcript


def get_transcript_with_yt_dlp(video_url, lang="pt"):
    """
    Baixa legenda automática via yt-dlp.
    Prefere formato VTT (timestamps confiáveis); fallback para json3.

    Retorna lista de dicts: [{'start': float, 'duration': float, 'text': str}, ...]
    Ou [] se não houver legenda disponível.
    """
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [lang],
        'outtmpl': '%(title)s.%(ext)s',
    }
    if COOKIES_FROM_BROWSER:
        ydl_opts['cookies_from_browser'] = COOKIES_FROM_BROWSER

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        captions = info.get('automatic_captions', {}) or info.get('subtitles', {})
        lang_caps = captions.get(lang, [])
        if not lang_caps:
            return []

        # Prefere VTT — timestamps explícitos e confiáveis
        cap = next((c for c in lang_caps if c.get('ext') == 'vtt'), None)
        fmt = 'vtt'
        if cap is None:
            cap = next((c for c in lang_caps if c.get('ext') == 'json3'), lang_caps[0])
            fmt = cap.get('ext', 'json3')

        sub_url = cap.get('url')
        if not sub_url:
            return []

        resp = requests.get(sub_url)
        if resp.status_code != 200:
            return []

        if fmt == 'vtt':
            return _parse_vtt(resp.text)
        else:
            return _parse_json3(resp.json())

def transcript_to_text(transcript):
    """Converte a transcrição em texto."""
    return ' '.join([entry['text'] for entry in transcript])

def get_video_metadata(url):
    """Extrai metadados completos de um vídeo do YouTube."""
    ydl_opts = {'quiet': True, 'skip_download': True}
    video_id = extract_video_id(url)

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        print_hex_color('#f92f60', f"❌ Erro ao extrair metadados: {e}")
        return None

    # Formatar data
    upload_date = info.get('upload_date')

    if upload_date:
        try:
            if "-" in upload_date:
                # Caso venha com hora
                upload_date = datetime.strptime(upload_date, "%Y%m%d-%H:%M").strftime("%d/%m/%Y %H:%M")
            else:
                # Caso venha só a data
                upload_date = datetime.strptime(upload_date, "%Y%m%d").strftime("%d/%m/%Y")
        except Exception:
            upload_date = "Formato inválido"
    else:
        upload_date = "Não informado"

    # Construir o dicionário com os dados
    metadata = {
        'transcription_by': 'YouTubeTranscriptApi',
        'api': 'youtube',
        'type_file': 'link',
        'source': url,
        'date_generated': datetime.now().isoformat(),
        'video_id': info.get('id'),
        'title': info.get('title'),
        'description': info.get('description'), # Tratamento
        'uploader': info.get('uploader'), # para notas, acho q o id seja mais interessante
        'uploader_id': info.get('uploader_id'), # sera q em outras redes o @ é o mesmo?
        #'channel_id': info.get('channel_id'), # Não usar
        'channel_url': info.get('channel_url'), # Usar para criar uma nota do canal (fururamente)
        'webpage_url': info.get('webpage_url'), # Link do video
        'date_upload': upload_date,
        'duration_sec': info.get('duration'),
        #'view_count': info.get('view_count'), # Não usar
        #'like_count': info.get('like_count'), # Não usar
        'categories': info.get('categories'),
        'thumbnail': info.get('thumbnail'),
        #'fps': info.get('fps'), # Não usar
        #'width': info.get('width'), # Não usar
        #'height': info.get('height'), # Não usar
        'filesize': info.get('filesize'), # Não usar
        #'license': info.get('license'), # Não usar
        'chapters': info.get('chapters'), #
        #'playable_in_embed': info.get('playable_in_embed'), # Não usar
        #'availability': info.get('availability'), # Não usar
        #'live_status': info.get('live_status') # Não usar
    }

    return metadata

def sanitize_filename(title, max_length=100):
    # Remove acentos e normaliza caracteres
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    # Remove caracteres inválidos para nomes de arquivo
    title = re.sub(r'[\\/*?:"<>|]', '_', title)
    # Substitui espaços duplos ou pontuações repetidas
    title = re.sub(r'\s+', ' ', title).strip()
    # Corta se for muito longo
    return title[:max_length]

def download_audio_from_youtube(url, output_dir="data/02. audio/Youtube", extension_file="mp3"):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        with YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            raw_title = info['title']
            safe_title = sanitize_filename(raw_title)
    except Exception as e:
        print_hex_color('#f92f60', f"❌ Erro ao baixar áudio: {e}")
        return None

    output_path = output_dir / safe_title

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,  # Sem extensão!
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': extension_file,
            'preferredquality': '192',
        }]
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print_hex_color('#f92f60', f"❌ Erro ao processar o áudio: {e}")
        return None

    return str(output_path) + f".{extension_file}"
