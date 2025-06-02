import streamlit as st
import os
import pandas as pd

from src.core.converter import *
from src.core.file_handler import *


# 🧠 Função para gerar status inicial
def gerar_status(videos):
    status = []
    for video in videos:
        base_path = video.replace("data\\01. videos\\", "").rsplit(".", 1)[0]
        video_name = video.split("\\")[-1]
        audio = f"data\\02. audio\\{base_path}.mp3"
        transcricao = f"data\\03. transcriptions\\{base_path}.json"
        nota = f"data\\04. notes\\{base_path}.md"
        #audio_mb = obter_informacoes_arquivos(audio)
        
        status.append({
            "Vídeo": video_name,
            "Video Path": video,
            "Audio Path": audio,
            #"Audio MB": audio_mb['tamanho_mb'],
            "Transcricao Path": transcricao,
            "Extrair Áudio": os.path.exists(audio),
            "Transcrever": os.path.exists(transcricao),
            "Gerar Nota": os.path.exists(nota),
        })
    return pd.DataFrame(status)


# 🎨 Config da página
st.set_page_config(
    page_title="Conversor de Aulas",
    page_icon="🎧",
    layout="wide"
)

st.title("🎧 Conversor de Aulas - Vídeo → Áudio → Transcrição → Nota")


# 🔍 Buscar arquivos
videos = listar_arquivos("data\\01. videos")
df = gerar_status(videos)

st.subheader("📁 Status dos Arquivos")

# 🔒 Define quais colunas ficam travadas
disabled = {
    "Extrair Áudio": df["Extrair Áudio"].tolist(),
    "Transcrever": df["Transcrever"].tolist(),
    "Gerar Nota": df["Gerar Nota"].tolist()
}

edit_df = st.data_editor(
    df.drop(columns=["Video Path", "Audio Path", "Transcricao Path"]),
    use_container_width=True,
    num_rows="dynamic",
    #disabled=disabled
)

# 🗂️ Coletar seleção feita na tabela editável
selecao = []
for _, row in edit_df.iterrows():
    selecao.append({
        "Vídeo": row["Vídeo"],
        "Video Path": df.loc[df["Vídeo"] == row["Vídeo"], "Video Path"].values[0],
        "Audio Path": df.loc[df["Vídeo"] == row["Vídeo"], "Audio Path"].values[0],
        "Transcricao Path": df.loc[df["Vídeo"] == row["Vídeo"], "Transcricao Path"].values[0],
        "Extrair Áudio": row["Extrair Áudio"] and not df.loc[df["Vídeo"] == row["Vídeo"], "Extrair Áudio"].values[0],
        "Transcrever": row["Transcrever"] and not df.loc[df["Vídeo"] == row["Vídeo"], "Transcrever"].values[0],
        "Gerar Nota": row["Gerar Nota"] and not df.loc[df["Vídeo"] == row["Vídeo"], "Gerar Nota"].values[0]
    })


st.divider()

st.subheader("💼 OU Processar Diretamente por Caminho")

caminho_manual = st.text_input("Digite o caminho do arquivo (vídeo, áudio ou transcrição)")

col_manual1, col_manual2, col_manual3 = st.columns(3)

processar_audio_manual = col_manual1.button("🎧 Extrair Áudio (Manual)")
processar_trans_manual = col_manual2.button("📜 Transcrever (Manual)")
processar_nota_manual = col_manual3.button("🗒️ Gerar Nota (Manual)")

if processar_audio_manual and caminho_manual:
    video_para_audio([caminho_manual])
    st.success("✅ Áudio gerado manualmente!")

if processar_trans_manual and caminho_manual:
    audio_para_transcricao([caminho_manual])
    st.success("✅ Transcrição gerada manualmente!")

if processar_nota_manual and caminho_manual:
    transcricao_para_nota([caminho_manual])
    st.success("✅ Nota gerada manualmente!")


st.divider()


# 🚀 Processamento em lote via checkboxes
if st.button("🚀 Executar Processamento Selecionado"):
    with st.spinner("Processando..."):
        for item in selecao:
            if item["Extrair Áudio"]:
                video_para_audio([item["Video Path"]])
            if item["Transcrever"]:
                audio_para_transcricao([item["Audio Path"]])
            if item["Gerar Nota"]:
                transcricao_para_nota([item["Transcricao Path"]])

    st.success("✅ Processamento concluído com sucesso!")

