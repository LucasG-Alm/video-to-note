from tqdm import tqdm
import time
from datetime import datetime
import os
import json
from groq import Groq
from src.utils.utils import *


def transcrever_audio(caminho_arquivo: str, idioma="pt", contexto="", model: str="whisper-large-v3-turbo"):
    client = Groq()
    #print_hex_color("#32CBFF", "📡 Enviando áudio para transcrição...")
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


if __name__ == "__main__":
    caminho_audio = "..\\..\\data\\02. audio\\Plataforma_Finclass\\01. Como funciona a Finclass - 2025-05-12 15-34-07.mp3"
    saida_json = "..\\..\\data\\03. transcriptions\\Plataforma_Finclass\\01. Como funciona a Finclass - 2025-05-12 15-34-07.json"
    os.makedirs("..\\..\\data\\03. transcriptions\\Plataforma_Finclass\\", exist_ok=True)

    model = "whisper-large-v3-turbo"
    transcricao = transcrever_audio(caminho_audio, idioma="pt", contexto="Curso de Finanças", model=model)
    #Add Modelo e arquivo de base para transcrição
    metadata = {
        "transcription_by": model,
        "type_file": 'local_file',
        "source": caminho_audio,
        "date_generated": datetime.now().isoformat()
    }

    salvar_transcricao(metadata, transcricao, saida_json)

    print_hex_color("#56D08A", "✅ Transcrição salva em: ", saida_json)


