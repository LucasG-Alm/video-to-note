import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from pydub import AudioSegment, silence
from tqdm import tqdm
import math
import os


def cortar_audio_em_wav_com_silencio(
    audio_path,
    tamanho_max_mb=25,
    min_silence_len=700,
    silence_thresh_adjust=-16,
    output_folder="output"
):
    # Cria a pasta de saída
    os.makedirs(output_folder, exist_ok=True)

    print("🔍 Carregando áudio...")
    audio = AudioSegment.from_wav(audio_path)
    tamanho_total_bytes = len(audio.raw_data)
    duracao_total_ms = len(audio)

    # Conversões
    bytes_por_ms = tamanho_total_bytes / duracao_total_ms
    ms_por_mb = (1 * 1024 * 1024) / bytes_por_ms

    # Detecta TODOS os silêncios uma vez só
    print("🔎 Detectando silêncios no áudio...")
    silencios = silence.detect_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=audio.dBFS + silence_thresh_adjust
    )
    silencios = [(start, end) for start, end in silencios]

    print(f"🧠 {len(silencios)} silêncios detectados no total.")

    partes = []
    offset_ms = 0
    parte_num = 1

    total_partes = math.ceil(tamanho_total_bytes / (tamanho_max_mb * 1024 * 1024))

    print(f"🚀 Gerando cerca de {total_partes} partes de até {tamanho_max_mb}MB.")

    with tqdm(total=total_partes, desc="Processando partes") as pbar:
        while offset_ms < duracao_total_ms:
            faixa_inicio = offset_ms + ms_por_mb * (tamanho_max_mb - 1)
            faixa_fim = offset_ms + ms_por_mb * tamanho_max_mb

            faixa_inicio = min(faixa_inicio, duracao_total_ms)
            faixa_fim = min(faixa_fim, duracao_total_ms)

            # Busca silêncio dentro da faixa
            silencio_ideal = None
            for start, _ in silencios:
                if faixa_inicio <= start <= faixa_fim:
                    silencio_ideal = start
                    break

            # Se não achou, corta no limite da faixa
            ponto_corte = silencio_ideal if silencio_ideal else faixa_fim

            print(
                f"✂️ Parte {parte_num}: {offset_ms/1000:.2f}s até {ponto_corte/1000:.2f}s "
                + (f"(silêncio encontrado)" if silencio_ideal else "(corte seco)")
            )

            parte = audio[offset_ms:ponto_corte]
            output_path = os.path.join(output_folder, f"parte_{parte_num}.wav")
            parte.export(output_path, format="wav")
            partes.append(output_path)

            offset_ms = ponto_corte
            parte_num += 1
            pbar.update(1)

    print("✅ Processamento concluído!")
    return partes

caminho = 'data\\02. audio\\Youtube\\Crescendo em meio a dor (ep.1).mp3'
cortes = cortar_por_tamanho_com_silencio(caminho, tamanho_max_mb=25)
