import re
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime


def extract_video_id(url):
    """Extrai o ID do vídeo do link do YouTube."""
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None


def get_video_metadata(video_id):
    """Pega metadados do vídeo: título, descrição, autor, data."""
    ydl_opts = {'quiet': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        return {
            'title': info.get('title', 'Sem título'),
            'description': info.get('description', ''),
            'channel': info.get('uploader', 'Desconhecido'),
            'upload_date': datetime.strptime(info.get('upload_date', '19700101'), '%Y%m%d').strftime('%d/%m/%Y')
        }


def extract_timestamps(description):
    """Extrai tópicos e timestamps da descrição."""
    pattern = re.compile(r'(\d{1,2}):(\d{2})\s+(.+)')
    timestamps = []
    for match in pattern.findall(description):
        minutes, seconds, title = match
        start_time = int(minutes) * 60 + int(seconds)
        timestamps.append((start_time, f"{minutes}:{seconds}", title.strip()))
    return timestamps


def get_transcript(video_id):
    """Pega a transcrição do vídeo."""
    try:
        return YouTubeTranscriptApi.get_transcript(video_id, languages=['pt'])
    except Exception as e:
        print(f"❌ Sem transcrição disponível: {e}")
        return []


def group_transcript_by_timestamps(transcript, timestamps):
    """Agrupa a transcrição com base nos tópicos da minutagem."""
    grouped = {}
    for i, (start_time, time_str, title) in enumerate(timestamps):
        end_time = timestamps[i + 1][0] if i + 1 < len(timestamps) else float('inf')
        grouped[(time_str, title)] = [
            entry['text'] for entry in transcript if start_time <= entry['start'] < end_time
        ]
    return grouped


def generate_markdown_note(metadata, timestamps, grouped_transcript, url):
    """Gera a nota em formato markdown."""

    data_hoje = datetime.now().strftime('%d/%m/%Y')

    # ==== HEADER ====
    header = f"""---
page: "[[YouTube]]"
Área: 
    - Aprendizado
tags:
    - #youtube
    - #{metadata['channel'].replace(' ', '_')}
Link: {url}
autor: "[[{metadata['channel']}]]"
data_nota: {data_hoje}
status:
revisao:
---
"""

    # ==== RESUMO ====
    resumo = "## Resumo:\nResumo não informado. (Gerar manualmente)\n\n"

    # ==== TERMOS ====
    termos = "### Termos e Referências Principais:\n- Não informado.\n\n"

    # ==== REFERÊNCIAS ====
    referencias = "### Referências e Links:\n- Não informado.\n\n"

    # ==== MINUTAGEM ====
    minutagem = "### Minutagem:\n"
    for (start_sec, time_str, title) in timestamps:
        minutagem += f"- {time_str} - **{title}**\n"
    minutagem += "\n"

    # ==== PALAVRAS-CHAVE ====
    palavras = "### Palavras-chave:\n- Não informado.\n\n"

    # ==== TRANSCRIÇÃO POR TÓPICO ====
    texto = ""
    for (time_str, title), linhas in grouped_transcript.items():
        texto += f"## {title}\n**[{time_str}]**\n\n"
        texto += "\n".join(linhas) + "\n\n---\n\n"

    nota_md = header + resumo + termos + referencias + minutagem + palavras + texto
    return nota_md


def save_markdown(filename, content):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)


