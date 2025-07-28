import os
from tqdm import tqdm
from moviepy import VideoFileClip
from pydub import AudioSegment, silence
from pydub.silence import split_on_silence


def extrair_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    # Codec correto para MP3
    audio.write_audiofile(audio_path, codec='libmp3lame', fps=44100)
    print(f"✅ Áudio extraído para: {audio_path}")

def cortar_audio_por_silencio(caminho_audio: str, pasta_saida="tmp\\audio", min_silence_len=700, silence_thresh=-40, keep_silence=500):
    #Corta o áudio em chunks usando os silêncios.
    #Retorna lista de caminhos dos arquivos cortados.

    title = caminho_audio.split('\\')[-1]

    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
    
    audio = AudioSegment.from_file(caminho_audio)
    chunks = split_on_silence(audio, 
                              min_silence_len=min_silence_len,
                              silence_thresh=silence_thresh,
                              keep_silence=keep_silence)

    arquivos_chunks = []
    for i, chunk in enumerate(chunks):
        chunk_path = os.path.join(pasta_saida, f"{title}_{i:03d}.wav")
        chunk.export(chunk_path, format="wav")
        arquivos_chunks.append(chunk_path)
    return arquivos_chunks

#Corta o áudio em chunks usando os silêncios após um tempo de audio ou tamanho de arquivo
#Retorna lista de caminhos dos arquivos cortados.
def cortar_audio_hibrido(
    arquivo_entrada,
    output_dir="data/02. audio/chunks",
    modo="tamanho",                # "tempo" ou "tamanho"
    duracao_max_min=15,            # minutos
    tamanho_max_mb=25,             # megabytes
    cortar_por_silencio=False,     # refinamento opcional
    min_silencio_len=1000,         # ms
    silencio_thresh=-40,           # dBFS
    keep_silence=500,              # ms
    formato_saida="mp3"
):
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n🎧 Carregando áudio: {arquivo_entrada}")
    audio = AudioSegment.from_file(arquivo_entrada)

    nome_base = os.path.splitext(os.path.basename(arquivo_entrada))[0]
    print(nome_base)

    # Configurações iniciais
    duracao_max_ms = duracao_max_min * 60 * 1000  # min -> ms
    tamanho_bytes_max = tamanho_max_mb * 1_000_000  # MB -> bytes

    print(f"⏳ Duração máxima configurada: {duracao_max_ms / 60000:.2f} minutos")
    print(f"💾 Tamanho máximo configurado: {tamanho_bytes_max / 1_000_000:.2f} MB")

    arquivo_bytes = len(audio.raw_data)  # bytes
    arquivo_ms = len(audio)  # duração em milissegundos

    arquivo_mb = arquivo_bytes / 1_000_000  # bytes -> MB
    arquivo_segundos = arquivo_ms / 1000  # ms -> segundos
    arquivo_minutos = arquivo_segundos / 60  # segundos -> minutos

    taxa_bytes_por_ms = arquivo_bytes / arquivo_ms  # bytes/ms
    taxa_bytes_por_segundo = taxa_bytes_por_ms * 1000  # bytes/segundo
    taxa_mb_por_segundo = taxa_bytes_por_segundo / 1_000_000  # MB/s
    taxa_mb_por_minuto = taxa_mb_por_segundo * 60  # MB/minuto

    print(f"🔍 Arquivo: {arquivo_mb:.2f} MB / {arquivo_minutos:.2f} minutos")
    print(f"🔍 Taxa de dados: {taxa_mb_por_minuto:.2f} MB/minuto")

    if modo == "tamanho":
        duracao_ms_max = int(tamanho_bytes_max / taxa_bytes_por_ms)
        print(f"📏 Cortando por tamanho: blocos de {duracao_ms_max / 60000:.2f} minutos (~{tamanho_max_mb} MB)")
    elif modo == "tempo":
        duracao_ms_max = duracao_max_ms
        print(f"📏 Cortando por tempo: blocos de {duracao_ms_max / 60000:.2f} minutos")
    else:
        raise ValueError("⚠️ Modo inválido. Use 'tempo' ou 'tamanho'.")



    print(f"📏 Cortando em blocos de {duracao_ms_max / 60000:.2f} min cada...")

    chunks = [
        audio[i:i + duracao_ms_max]
        for i in range(0, len(audio), duracao_ms_max)
    ]

    print(f"🔪 Total de {len(chunks)} blocos gerados inicialmente.")

    arquivos_chunks = []
    contador = 1

    for chunk in tqdm(chunks, desc="🚀 Processando chunks"):
        if cortar_por_silencio:
            sub_chunks = silence.split_on_silence(
                chunk,
                min_silence_len=min_silencio_len,
                silence_thresh=silencio_thresh,
                keep_silence=keep_silence
            )
            if not sub_chunks:
                sub_chunks = [chunk]
        else:
            sub_chunks = [chunk]

        for sub in sub_chunks:
            caminho_saida = os.path.join(
                output_dir,
                f"{nome_base}_chunk_{contador:03}.{formato_saida}"
            )
            sub.export(caminho_saida, format=formato_saida)
            arquivos_chunks.append(caminho_saida)
            print(f"✅ Gerado: {caminho_saida}")
            contador += 1

    print(f"\n🚀 Total de {len(arquivos_chunks)} arquivos gerados no diretório: {output_dir}")
    return arquivos_chunks


if __name__ == "__main__":
    #video = "src/01. video_aulas/Plataforma_Finclass/Trilha-Primeiros Passos/Inteligência Financeira/02. Corrigindo Vícios Sociais - 2025-05-13 15-49-58.mkv"
    #mp3 = video.replace("01. video_aulas", "02. audio").split(".")[0]
    #os.makedirs("/".join(video).split("/")[:-1], exist_ok=True)
    #extrair_audio(video, mp3)

    cortar_audio_hibrido(
        arquivo_entrada="D:\\Users\\Lucas\\OneDrive\\Documentos\\PROGRAMAÇÃO\\Python\\Doc courses\\data\\02. audio\\Youtube\\Crescendo em meio a dor (ep.1).mp3",
        modo="tamanho",
        tamanho_max_mb=25,
        cortar_por_silencio=False,  # Opcional
    )