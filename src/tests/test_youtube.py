import os
import time
import random
from pathlib import Path

from src.services.youtube import *
from src.core.notes2 import gerar_nota_md

PROJECT_ROOT = Path(__file__).parent.parent.parent

def Youtube_to_Notes(url_videos:list, model:str='llama-3.3-70b-versatile', pasta_destino:str=''):
    for url in url_videos:
        # 🔥 EXECUÇÃO
        url = url #"https://www.youtube.com/watch?v=XswU6CRs79s"
        video_id = extract_video_id(url)

        if video_id:
            metadata = get_video_metadata(url)
            title = sanitize_filename(metadata['title'])
            print(title)
            transcript = get_transcript_with_yt_dlp(video_id)
            #print(transcript)

            if transcript:
                final_transcript = {
                    'text': transcript_to_text(transcript),
                    'segments': transcript
                }
            else:
                print_hex_color('#f92f60', "❌ Sem legenda disponível, tentando Whisper...")
                print_hex_color("#ffaa00", "⚠️  Baixando áudio para transcrição com Whisper...")

                audio_path_result = download_audio_from_youtube(url)
                if audio_path_result:
                    final_transcript = transcrever_audio_inteligente(audio_path_result)
                else:
                    print_hex_color('#f92f60', "❌ Não foi possível baixar o áudio nem transcrever.")
                    final_transcript = {'text': '', 'segments': []}

                metadata['transcription_by'] = 'Groq Whisper API'

            json_path = PROJECT_ROOT / "data/03. transcriptions/Youtube" / pasta_destino / f"{title}.json"
            salvar_transcricao(metadata, final_transcript, str(json_path))

            try:
                gerar_nota_md(
                    path_transcricao_json=str(json_path),
                    path_template_md=str(PROJECT_ROOT / "templates/template_youtube copy.md"),
                    metadata={
                        "tags_md": "YouTube/Vídeo"
                    },
                    model=model
                )
            except Exception as e:
                print_hex_color('#f92f60', f"❌ Erro ao gerar nota: {e}")
                pass

        else:
            print_hex_color('#f92f60', "❌ Não foi possível extrair o ID do vídeo.")

        delay = random.uniform(90, 150)
        print(f"Aguardando {round(delay,2)} segundos pra não tomar bloco 🚫")
        time.sleep(delay)

if __name__ == "__main__":
    # Lista de vídeos
    videos = [
        #"https://www.youtube.com/shorts/2DGce61n8rY",
    ]
    Youtube_to_Notes(videos)

Links = {
    '2025-07-14': [
        'https://www.youtube.com/watch?v=UPnw_AG78j8',
        'https://www.youtube.com/watch?v=GIOriGOS0tc',
        'https://www.youtube.com/watch?v=DftE8SBbNqY&t=4s'
        'https://www.youtube.com/watch?v=C38xlWnkezQ',
        'https://www.youtube.com/watch?v=HvWsUDbAAgs',
        'https://www.youtube.com/watch?v=uacS7abgN8k&t=922s'
        'https://www.youtube.com/watch?v=dCMs_TRzNaE',
        'https://www.youtube.com/watch?v=H5FNS4mIKQM&t=736s'
    ],
    '2025-07-15': [
        'https://www.youtube.com/watch?v=H5FNS4mIKQM&t=736s'
    ],
    '2025-07-16':[
        'https://www.youtube.com/watch?v=2BpkWc-6R-w&t=5845s&pp=0gcJCcwJAYcqIYzv'
    ],
    '2025-07-17':[
        'https://www.youtube.com/watch?v=V6nCJF8j944&t=468s'
        'https://www.youtube.com/watch?v=2Nor4OJP4gk',
        'https://www.youtube.com/watch?v=syN9_Qm7Cwk&t=486s',
    ],
    '2025-07-18':[
        'https://www.youtube.com/watch?v=qFYc2oKiAIg',
        'https://www.youtube.com/watch?v=EISKL0MWnSo',
        'https://www.youtube.com/watch?v=_5z7f3lEoF4&t=37s',
        'https://www.youtube.com/watch?v=a1MVf8eGlG8',
        'https://www.youtube.com/watch?v=l8zh-v3FIpM'
    ],
    '2025-07-19':[
        'https://www.youtube.com/watch?v=DE89rftYaBU&t=2s'
    ]
}

def processar_links(links_dict):
    for folder, links in links_dict.items():
        (PROJECT_ROOT / "data/03. transcriptions/Youtube" / folder).mkdir(parents=True, exist_ok=True)
        (PROJECT_ROOT / "data/04. notes/Youtube" / folder).mkdir(parents=True, exist_ok=True)
        
        try:
            print(f"🔁 Processando folder: {folder}")
            Youtube_to_Notes(links, pasta_destino=folder)
        except Exception as e:
            print(f"❌ Erro ao processar {links}: {e}")

if __name__ == "__main__":
    processar_links(Links)