import re
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime
from pprint import pprint
import json
import tqdm

from transcription import *

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

def transcript_to_text(transcript):
    """Converte a transcrição em texto."""
    return ' '.join([entry['text'] for entry in transcript])

def get_video_metadata(url):
    """Extrai metadados completos de um vídeo do YouTube."""
    ydl_opts = {'quiet': True, 'skip_download': True}
    video_id = extract_video_id(url)

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_id, download=False)


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
        #'tags': info.get('tags'), # Não usar
        'thumbnail': info.get('thumbnail'), # anexar a nota
        #'thumbnails': info.get('thumbnails'), # não usar
        #'subtitles': info.get('subtitles'), # Não é a transcrição?
        #'automatic_captions': info.get('automatic_captions'),# Não é a transcrição?
        #'fps': info.get('fps'), # Não usar
        #'width': info.get('width'), # Não usar
        #'height': info.get('height'), # Não usar
        #'filesize': info.get('filesize'), # Não usar
        #'license': info.get('license'), # Não usar
        'chapters': info.get('chapters'), #
        #'playable_in_embed': info.get('playable_in_embed'), # Não usar
        #'availability': info.get('availability'), # Não usar
        #'live_status': info.get('live_status') # Não usar
    }

    return metadata


def download_audio_from_youtube(url, output_dir="data\\02. audio\\Youtube", extension_file="mp3"):
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': extension_file,
            'preferredquality': '192',
        }]
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return os.path.join(output_dir, f"{info['title']}.{extension_file}")

# 🔥 EXECUÇÃO
url = "https://www.youtube.com/watch?v=sWI_7B0PO5g"
video_id = extract_video_id(url)

if video_id:
    metadata = get_video_metadata(url)
    title = re.sub(r'[\\/*?:"<>|]', "_", metadata['title'])
    transcript = get_transcript(video_id)

    if transcript:
        final_transcript = {
            'text': transcript_to_text(transcript),
            'segments': transcript
        }
    else:
        # Baixa o áudio e transcreve com Whisper da Groq
        audio_path = f"data\\02. audio\\Youtube\\{title}.mp3"
        print_hex_color("#ffaa00", "⚠️  Baixando áudio para transcrição com Whisper...")
        download_audio_from_youtube(url)

        final_transcript = transcrever_audio(audio_path)

        metadata['transcription_by'] = 'Groq Whisper API'

    salvar_transcricao(metadata, final_transcript, f'data\\03. transcriptions\\Youtube\\{title}.json')
    print_hex_color('#0bd271', f"✅ Transcrição salva com sucesso.")

else:
    print_hex_color('#f92f60', "❌ Não foi possível extrair o ID do vídeo.")