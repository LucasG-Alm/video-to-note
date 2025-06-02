import os
import tqdm

from src.core.audio import *
from src.core.notes import *
from src.core.file_handler import *

from src.services.transcription import *

#Video -> Audio
#videos = listar_arquivos("src\\01. video_aulas")

def video_para_audio(videos: list):
    for video in tqdm(videos):
        mp3 = ".".join(video.replace("01. video_aulas", "02. audio").split(".")[:-1]) + ".mp3"
        pasta = "/".join(video.split("\\")[:-1])
        os.makedirs("/".join(video.split("\\")[:-1]), exist_ok=True)
        extrair_audio(video, mp3)

#Audio -> Transcrições
#audios = listar_arquivos("src\\02. audio")

def audio_para_transcricao(audios: list):
    for audio in tqdm(audios):
        nome_base = os.path.basename(audio).rsplit(".", 1)[0]
        pasta_transcricao = "\\".join(audio.replace("02. audio", "03. transcrições").split("\\")[:-1])
        os.makedirs(pasta_transcricao, exist_ok=True)

        caminho_arquivo = os.path.join(pasta_transcricao, f"{nome_base}.json")
        model = "whisper-large-v3-turbo"
        transcricao = transcrever_audio(audio, idioma="pt", contexto="Curso de Finanças", model=model)
        print(type(transcricao))
        
        #Add Modelo e arquivo de base para transcrição
        transcricao = {'transcription_by': model,
                       'font': f'local_file: {audio}', 
                       **transcricao
                      }
        
        salvar_transcricao(transcricao, caminho_arquivo)

        print_hex_color("#56D08A", "✅ Transcrição salva em: ", pasta_transcricao)

# Transcrições in Notas
#transcricoes = listar_arquivos("src/03. transcricoes")

def transcricao_para_nota(transcricoes: list):
    for transcricao in transcricoes:
        gerar_nota_md(transcricao, prompt_task, "Finanças", ["Curso", "Finanças/Finclass/Finclasses"])

