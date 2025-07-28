import streamlit as st

def main():
    st.title("VIDEO TO NOTES")

    # Criar uma linha horizontal com os dois botões e a caixa de texto no meio
    col1, col2, col3 = st.columns([1,6,1])  # Espaço proporcional pra ficar legal

    with col1:
        # Botão de anexar vídeo - ao clicar, abre explorador de arquivos (aceitando vídeos)
        video_file = st.file_uploader("Anexos", type=['mp4', 'avi', 'mov', 'mkv'], key="upload_video")

    with col2:
        # Caixa de texto para colar link do Youtube
        yt_link = st.text_input("Cole o link do YouTube aqui")

    with col3:
        # Botão enviar - só ativa se tiver link
        if st.button("Enviar"):
            if yt_link.strip() == "":
                st.warning("Coloque um link do YouTube antes de enviar!")
            else:
                st.success(f"Link enviado: {yt_link}")
                # Aqui você coloca o que quiser fazer com o link, tipo começar a processar

    # Mostrar um preview do vídeo carregado (opcional)
    if video_file is not None:
        st.video(video_file)

if __name__ == "__main__":
    main()
