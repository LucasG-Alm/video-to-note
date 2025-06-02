from moviepy import VideoFileClip
import os

def extrair_audio(video_path, mp3_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    # Codec correto para MP3
    audio.write_audiofile(mp3_path, codec='libmp3lame', fps=44100)
    print(f"✅ Áudio extraído para: {mp3_path}")

if __name__ == "__main__":
    video = "src/01. video_aulas/Plataforma_Finclass/Trilha-Primeiros Passos/Inteligência Financeira/02. Corrigindo Vícios Sociais - 2025-05-13 15-49-58.mkv"
    mp3 = video.replace("01. video_aulas", "02. audio").split(".")[0]
    os.makedirs("/".join(video).split("/")[:-1], exist_ok=True)
    extrair_audio(video, mp3)
