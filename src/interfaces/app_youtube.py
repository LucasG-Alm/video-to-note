import streamlit as st
from services.youtube import *

st.set_page_config(page_title="YouTube → Nota", page_icon="🎥")

st.title("🎥 YouTube → Transcrição → 📒 Nota Markdown")

url = st.text_input("Cole o link do vídeo do YouTube:")

if url:
    video_id = extract_video_id(url)
    if video_id:
        with st.spinner("🔍 Buscando dados do vídeo..."):
            video_info = get_video_description(video_id)
            transcript = get_transcript(video_id)
            timestamps = extract_timestamps(video_info['description'])
            grouped = group_transcript_by_timestamps(transcript, timestamps)

        st.success(f"🎯 Vídeo: {video_info['title']}")

        st.subheader("📝 Prévia da Nota")
        for (time_str, title), lines in grouped.items():
            st.markdown(f"### {title} ({time_str})")
            st.markdown(" ".join(lines))
            st.markdown("---")

        if st.button("💾 Gerar Nota Markdown"):
            filename = f"{video_info['title'].replace(' ', '_')}.md"
            save_transcript_to_markdown(filename, video_info, timestamps, grouped)
            st.success(f"✅ Nota salva como {filename}")
    else:
        st.error("❌ Link inválido ou não reconhecido.")
