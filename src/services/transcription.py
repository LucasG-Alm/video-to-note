import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from tqdm import tqdm
import time
from datetime import datetime
import os
import json
from groq import Groq
from pydub import AudioSegment
from src.core.audio import cortar_audio_por_silencio, cortar_audio_hibrido

#from src.utils.utils import *
def print_hex_color(hex_color, msg, msg2=""):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    print(f"\033[38;2;{r};{g};{b}m{msg}\033[0m {msg2}")

def transcrever_audio(caminho_arquivo: str, idioma="pt", contexto="", model: str="whisper-large-v3-turbo"):
    client = Groq() # caso mudar a api de consumo, mudar a api dos metadados
    print(f'\033[38;2;50;203;255m📡 Enviando áudio para transcrição...\033[0m')

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

def transcrever_audio_inteligente(caminho_audio: str, idioma="pt", contexto="", model="whisper-large-v3-turbo", limite_mb=25):
    """
    Pipeline principal:
    - Se arquivo <= limite_mb transcreve direto
    - Se > limite_mb corta por silêncio, transcreve cada chunk e junta o texto
    """
    tamanho_mb = os.path.getsize(caminho_audio) / (1024 * 1024)
    print(f"Tamanho do áudio: {tamanho_mb:.2f} MB")

    if tamanho_mb <= limite_mb:
        print("Arquivo pequeno, transcrevendo direto...")
        return transcrever_audio(caminho_audio, idioma, contexto, model)
    
    print("Arquivo grande demais, cortando e transcrevendo chunks...")
    arquivos_chunks = cortar_audio_hibrido(
        caminho_audio,
        modo="tamanho",
        tamanho_max_mb=limite_mb,
        cortar_por_silencio=False  # Opcional
        )

    transcricoes = []
    for chunk_path in arquivos_chunks:
        resultado = transcrever_audio(chunk_path, idioma, contexto, model)
        print(resultado)
        texto = resultado.text # ajustar conforme retorno real da API
        transcricoes.append(texto)
    
    texto_final = "\n\n".join(transcricoes)
    
    # Opcional: salvar texto final num arquivo
    with open("transcricao_final.txt", "w", encoding="utf-8") as f:
        f.write(texto_final)
    
    print(f"Transcrição final compilada em 'transcricao_final.txt'")
    return {"text": texto_final}

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

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
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





