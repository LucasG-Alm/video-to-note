import sys
import os
import time
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.converter import video_para_audio, audio_para_transcricao
from src.core.file_handler import listar_arquivos
from src.utils.utils import print_hex_color


#videos = listar_arquivos('data\\01. videos')
#video_para_audio(videos)


import mimetypes
#mimetype, _ = mimetypes.guess_type("data\\02. audio\\Plataforma_Finclass\\01. Como funciona a Finclass - 2025-05-12 15-34-07.mp3")
#print(mimetype)

#from pydub.utils import mediainfo
#info = mediainfo("data\\02. audio\\Vídeo do WhatsApp de 2025-07-05 à(s) 02.31.08_1446e813.mp3")
#print(info["codec_name"])  # Deve mostrar "mp3"

audios = listar_arquivos('data\\02. audio')
audio_para_transcricao(audios)