import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.file_handler import *

audio_dir = obter_informacoes_arquivos('C:\\Users\\lucas\\OneDrive\\Documentos\\PROGRAMAÇÃO\\Python\\Doc courses\\data\\02. audio')
df_audio_dir = pd.DataFrame(audio_dir)
df_audio_dir.to_excel('audios.xlsx')