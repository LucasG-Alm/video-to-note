from tqdm import tqdm
import time
from datetime import datetime
import os
import json
from groq import Groq
from pydub import AudioSegment

#from src.utils.utils import *
def print_hex_color(hex_color, msg, msg2=""):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    print(f"\033[38;2;{r};{g};{b}m{msg}\033[0m {msg2}")

def transcrever_audio(caminho_arquivo: str, idioma="pt", contexto="", model: str="whisper-large-v3-turbo"):
    client = Groq() # caso mudar a api de consumo, mudar a api dos metadados
    print(f'\033[38;2;50;203;255m 📡 Enviando áudio para transcrição...\033[0m')

    # Barra de progresso fake enquanto espera a Groq responder
    with open(caminho_arquivo, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=file,
            model=model,
            prompt=contexto,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
            language=idioma,
            temperature=0.0
        )
        #print(json.dumps(transcription, indent=2, default=str))
    return transcription

def salvar_transcricao(metadata: dict, transcription, caminho_saida: str):
    def conversao_forcada(obj):
        try:
            return obj.__dict__
        except:
            return str(obj)

    transcription_dict = {
        'metadata': metadata,
        'transcription': dict(transcription)
    }

    with open(caminho_saida, "w", encoding="utf-8") as f:
        json.dump(
            transcription_dict,
            f,
            indent=2,
            ensure_ascii=False,
            default=conversao_forcada,
            separators=(",", ": ")
        )
    
    print_hex_color("#0bd271", "✅ Transcrição salva em: ", caminho_saida)


if __name__ == "__main__":
    caminho_audio = "data\\02. audio\\Plataforma_Finclass\\01. Como funciona a Finclass - 2025-05-12 15-34-07.mp3"
    saida_json = "data\\03. transcriptions\\Plataforma_Finclass\\01. Como funciona a Finclass - 2025-05-12 15-34-07.json"
    os.makedirs("data\\03. transcriptions\\Plataforma_Finclass\\", exist_ok=True)

    model = "whisper-large-v3-turbo"
    transcricao = transcrever_audio(caminho_audio, idioma="pt", contexto="Curso de Finanças", model=model)
    nome_base = os.path.basename(caminho_audio).rsplit(".", 1)[0]
    duracao_segundos = len(AudioSegment.from_mp3(caminho_audio)) / 1000
    info = os.stat(caminho_audio)
    
    #Add Modelo e arquivo de base para transcrição
    metadata = {
        "transcription_by": model,
        "api": 'groq', # caso mudar a api de consumo, mudar aqui
        "type_file": 'local_file',
        "source": caminho_audio,
        "date_generated": datetime.now().strftime("%d/%m/%Y %H:%M"),
        'title': nome_base,
        'duration_sec': duracao_segundos,
        'date_create_file': datetime.fromtimestamp(info.st_ctime).strftime("%d/%m/%Y %H:%M"),
        'size_file_mb': round(info.st_size / (1024 * 1024), 2)
    }

    salvar_transcricao(metadata, transcricao, saida_json)

    print("✅ Transcrição salva em: ", saida_json)


