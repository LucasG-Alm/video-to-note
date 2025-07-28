import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.services.transcription import *


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