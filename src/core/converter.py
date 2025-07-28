import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import tqdm

from src.core.audio import *
from src.core.notes import *
from src.core.file_handler import *

from src.services.transcription import *
from src.services.youtube import *

#Video -> Audio
#videos = listar_arquivos("src\\01. video_aulas")

def video_para_audio(videos: list):
    for video in tqdm(videos):
        mp3 = ".".join(video.replace("01. videos", "02. audio").split(".")[:-1]) + ".mp3"
        pasta = "/".join(mp3.split("\\")[:-1])
        os.makedirs(pasta, exist_ok=True)
        extrair_audio(video, mp3)

#Audio -> Transcrições
#audios = listar_arquivos("src\\02. audio")

def audio_para_transcricao(audios: list, model:str="whisper-large-v3-turbo"):
    for audio in tqdm(audios):
        print(f'\n{audio}')
        nome_base = os.path.basename(audio).rsplit(".", 1)[0]
        pasta_transcricao = "\\".join(audio.replace("02. audio", "03. transcriptions").split("\\")[:-1])
        #print(pasta_transcricao)
        os.makedirs(pasta_transcricao, exist_ok=True)

        caminho_audio = audio #os.path.join(pasta_transcricao, f"{nome_base}.json")
        transcricao = transcrever_audio(caminho_audio, idioma="pt", contexto="Curso de Finanças", model=model)
        # nome_base = os.path.basename(caminho_audio).rsplit(".", 1)[0]
        duracao_segundos = len(AudioSegment.from_mp3(caminho_audio)) / 1000
        info = os.stat(caminho_audio)
        
        # Add Modelo e arquivo de base para transcrição
        metadata = {
            'transcription_by': model,
            'api': 'groq', # caso mudar a api de consumo, mudar aqui
            'type_file': 'local_file',
            'source': caminho_audio,
            'date_generated': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'title': nome_base,
            'duration_sec': duracao_segundos,
            'date_create_file': datetime.fromtimestamp(info.st_ctime).strftime("%d/%m/%Y %H:%M"),
            'size_file_mb': round(info.st_size / (1024 * 1024), 2)
        }

        salvar_transcricao(metadata, transcricao, os.path.join(pasta_transcricao, f"{nome_base}.json"))

        print_hex_color("#56D08A", "✅ Transcrição salva em: ", pasta_transcricao)


#Link YouTube -> Transcrições
def linkyt_para_transcricao(links: list):
    for link in tqdm(links):
        metadata = get_video_metadata(video_id)
        title = re.sub(r'[\\/*?:"<>|]', "_", metadata['title'])
        pasta_transcricao = f'data\\03. transcriptions\\Youtube\\{title}.json'
        os.makedirs(pasta_transcricao, exist_ok=True)

        transcript = {
            'text': transcript_to_text(get_transcript(video_id)),
            'segments': get_transcript(video_id)
        }

        salvar_transcricao(metadata, transcript, pasta_transcricao)


# Transcrições in Notas
#transcricoes = listar_arquivos("src/03. transcricoes")

def transcricao_para_nota(transcricoes: list):
    for transcricao in transcricoes:
        gerar_nota_md(transcricao, prompt_task, "Finanças", ["Curso", "Finanças/Finclass/Finclasses"])