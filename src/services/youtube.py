import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import re
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime
from pprint import pprint
import unicodedata

from src.services.transcription import transcrever_audio, transcrever_audio_inteligente, salvar_transcricao

def print_hex_color(hex_color, msg, msg2=""):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    print(f"\033[38;2;{r};{g};{b}m{msg}\033[0m {msg2}")

def extract_video_id(url):
    """Extrai o ID do vídeo do link do YouTube."""
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

def get_transcript(video_id):
    """Pega a transcrição do vídeo."""
    try:
        return YouTubeTranscriptApi.get_transcript(video_id, languages=['pt'])
    except Exception as e:
        print_hex_color('#f92f60', f"❌ Sem transcrição disponível: {e}")
        return []

def get_transcript_with_yt_dlp(video_url, lang="pt"):
    """
    Tenta baixar legenda automática via yt-dlp + plugin SABR (yt-dlp-ytse).
    Retorna lista de dicts tipo:
    [{'start': 0.0, 'duration': 2.0, 'text': 'texto...'}, ...]
    Ou [] se não conseguir.
    """
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [lang],
        'subtitlesformat': 'json3',
        'cookiefile': '.cookies.txt',
        'outtmpl': '%(title)s.%(ext)s',
        'cookies_from_browser': 'edge'
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        # Legendas automáticas vem em info['automatic_captions'][lang] ou info['subtitles'][lang]
        captions = info.get('automatic_captions', {}) or info.get('subtitles', {})
        lang_caps = captions.get(lang, [])
        if not lang_caps:
            return []

        # Pega a url do subtitle json3
        sub_url = lang_caps[0].get('url')
        if not sub_url:
            return []

        import requests
        resp = requests.get(sub_url)
        if resp.status_code != 200:
            return []

        data = resp.json()
        # data['events'] é uma lista com 'segs' contendo textos
        transcript = []
        for event in data.get('events', []):
            text = ''.join(seg.get('utf8', '') for seg in event.get('segs', []))
            if text.strip():
                transcript.append({
                    'start': event.get('t', 0) / 1000,  # converte miliseg pra seg
                    'duration': event.get('d', 0) / 1000,
                    'text': text.strip()
                })
        return transcript

def transcript_to_text(transcript):
    """Converte a transcrição em texto."""
    return ' '.join([entry['text'] for entry in transcript])

def get_video_metadata(url):
    """Extrai metadados completos de um vídeo do YouTube."""
    ydl_opts = {'quiet': True, 'skip_download': True}
    video_id = extract_video_id(url)

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_id, download=False)
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
        'categories': info.get('categories'), # talvez usar...
        'tags': info.get('tags'), # Não usar
        'thumbnail': info.get('thumbnail'), # anexar a nota
        #'thumbnails': info.get('thumbnails'), # não usar
        'subtitles': info.get('subtitles'), # Não é a transcrição?
        'automatic_captions': info.get('automatic_captions'),# Não é a transcrição?
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

def download_audio_from_youtube(url, output_dir="data\\02. audio\\Youtube", extension_file="mp3"):
    os.makedirs(output_dir, exist_ok=True)
    try:
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=True)
            raw_title = info['title']
            safe_title = sanitize_filename(raw_title)
    except Exception as e:
        print_hex_color('#f92f60', f"❌ Erro ao baixar áudio: {e}")
        return None

    output_path = os.path.join(output_dir, safe_title)

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

    return output_path + f".{extension_file}"
