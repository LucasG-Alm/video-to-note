import re
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime
from pprint import pprint
import json
import tqdm

def extract_video_id(url):
    """Extrai o ID do vídeo do link do YouTube."""
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

def get_transcript(video_id):
    """Pega a transcrição do vídeo."""
    try:
        return YouTubeTranscriptApi.get_transcript(video_id, languages=['pt'])
    except Exception as e:
        print(f"❌ Sem transcrição disponível: {e}")
        return []

def transcript_to_text(transcript):
    """Converte a transcrição em texto."""
    return ' '.join([entry['text'] for entry in transcript])

def get_video_metadata(url):
    """Extrai metadados completos de um vídeo do YouTube."""
    ydl_opts = {'quiet': True, 'skip_download': True}

    with tqdm.tqdm(total=1, desc="Extraindo metadados") as pbar:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            pbar.update(1)

    # Formatar data
    upload_date = info.get('upload_date')
    if upload_date:
        upload_date = datetime.strptime(upload_date, "%Y%m%d").strftime("%d/%m/%Y")
    else:
        upload_date = "Não informado"

    # Construir o dicionário com os dados
    metadata = {
        'transcription_by': 'YouTubeTranscriptApi',
        'font': 'link-youtube',
        'video_id': info.get('id'),
        'title': info.get('title'),
        'description': info.get('description'), # Tratamento
        'uploader': info.get('uploader'), # para notas, acho q o id seja mais interessante
        'uploader_id': info.get('uploader_id'), # sera q em outras redes o @ é o mesmo?
        #'channel_id': info.get('channel_id'), # Não usar
        'channel_url': info.get('channel_url'), # Usar para criar uma nota do canal (fururamente)
        'webpage_url': info.get('webpage_url'), # Link do video
        'upload_date': upload_date,
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
        'text': transcript_to_text(get_transcript(video_id)),
        'segments': get_transcript(video_id)
    }

    return metadata

# 🔥 EXECUÇÃO
url = "https://www.youtube.com/watch?v=C67qPfI8_hg"
video_id = extract_video_id(url)

if video_id:
    meta = get_video_metadata(video_id)
    pprint(meta)
    title = re.sub(r'[\\/*?:"<>|]', "_", meta['title'])
    with open(f"{title}.json", 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=4)

    
    timestamps = meta['chapters'] # se false, pegar a transcrição e pedir para a IA fazer

    transcript = get_transcript(video_id)
    pprint(transcript)

    grouped = transcript_to_text(transcript)
    pprint(grouped)

else:
    print("❌ Não foi possível extrair o ID do vídeo.")
