"""
Testes unitários para src/pipeline.py

Testamos resolve_template — a função que mapeia um nível de profundidade
para o caminho absoluto do template correto no disco.

Por que testar isso?
→ Se alguém renomear um template ou errar no mapeamento, todos os
  processamentos de um determinado depth vão silenciosamente usar
  o template errado (ou explodir com FileNotFoundError em runtime).
  Melhor descobrir aqui.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.pipeline import resolve_template, DEPTH_TEMPLATES


class TestResolveTemplate:
    """
    resolve_template recebe um depth (str) e retorna o caminho absoluto
    do template .md correspondente.

    Pseudo-código:
        recebe depth
        busca filename em DEPTH_TEMPLATES (fallback: template_youtube_intermediario.md)
        monta caminho: PROJECT_ROOT / "templates" / filename
        verifica se o arquivo existe no disco
        retorna caminho como string (ou levanta FileNotFoundError)
    """

    def test_raso_aponta_para_template_correto(self):
        # Cada depth tem seu próprio template — confirma o mapeamento
        resultado = resolve_template("raso")
        assert resultado.endswith("template_youtube_raso.md")

    def test_intermediario_aponta_para_template_correto(self):
        resultado = resolve_template("intermediario")
        assert resultado.endswith("template_youtube_intermediario.md")

    def test_avancado_aponta_para_template_correto(self):
        resultado = resolve_template("avancado")
        assert resultado.endswith("template_youtube_avancado.md")

    def test_metacognitivo_aponta_para_template_correto(self):
        resultado = resolve_template("metacognitivo")
        assert resultado.endswith("template_youtube_metacognitivo.md")

    def test_todos_os_templates_existem_no_disco(self):
        # Garante que nenhum template foi renomeado ou deletado acidentalmente
        for depth in DEPTH_TEMPLATES:
            caminho = resolve_template(depth)
            assert Path(caminho).exists(), f"Template ausente para depth='{depth}': {caminho}"

    def test_depth_desconhecido_cai_no_intermediario(self):
        # DEPTH_TEMPLATES.get(depth, fallback) — depth inválido não deve explodir
        resultado = resolve_template("nao_existe")
        assert resultado.endswith("template_youtube_intermediario.md")

    def test_retorna_string(self):
        # gerar_nota_md espera str, não Path
        resultado = resolve_template("raso")
        assert isinstance(resultado, str)


class TestYoutubeToNotesTranscriptionCache:
    """
    BUG-02 — youtube_to_notes deve pular o download da transcrição
    quando um JSON de transcrição já existe em disco para aquele vídeo.

    Por que isso importa?
    → Re-baixar a legenda é lento e desnecessário. Se a transcrição já
      foi feita, queremos apenas regenerar a nota (ex: com depth diferente).
    → Permite usar JSONs de projetos antigos sem re-transcrever.
    """

    def _make_metadata(self):
        return {
            "title": "Video Cache Test",
            "uploader": "Canal",
            "webpage_url": "https://youtube.com/watch?v=cacheid",
            "duration_sec": 300,
            "chapters": [],
        }

    def test_pula_download_quando_json_existe(self, tmp_path):
        """Se o JSON de transcrição já existe, get_transcript_with_yt_dlp não é chamado."""
        from src.pipeline import youtube_to_notes

        metadata = self._make_metadata()
        transcricao_json = {
            "metadata": metadata,
            "transcription": {"text": "conteudo ja transcrito", "segments": []}
        }

        # JSON já existe no disco (simulando transcrição prévia)
        # Caminho espelhando PROJECT_ROOT / "data/03. transcriptions/Youtube"
        json_dir = tmp_path / "data" / "03. transcriptions" / "Youtube"
        json_dir.mkdir(parents=True)
        json_path = json_dir / "Video Cache Test.json"
        json_path.write_text(json.dumps(transcricao_json), encoding="utf-8")

        with patch("src.pipeline.extract_video_id", return_value="cacheid"), \
             patch("src.pipeline.get_video_metadata", return_value=metadata), \
             patch("src.pipeline.sanitize_filename", return_value="Video Cache Test"), \
             patch("src.pipeline.get_transcript_with_yt_dlp") as mock_transcript, \
             patch("src.pipeline.gerar_nota_md", return_value=tmp_path / "nota.md"), \
             patch("src.pipeline.salvar_transcricao"), \
             patch("src.pipeline.PROJECT_ROOT", tmp_path):

            youtube_to_notes(url="https://youtube.com/watch?v=cacheid")

        mock_transcript.assert_not_called()

    def test_faz_download_quando_json_nao_existe(self, tmp_path):
        """Se o JSON não existe, o fluxo normal de transcrição é executado."""
        from src.pipeline import youtube_to_notes

        metadata = self._make_metadata()
        transcript_segments = [{"start": 0.0, "duration": 5.0, "text": "ola"}]

        with patch("src.pipeline.extract_video_id", return_value="cacheid"), \
             patch("src.pipeline.get_video_metadata", return_value=metadata), \
             patch("src.pipeline.sanitize_filename", return_value="Video Cache Test"), \
             patch("src.pipeline.get_transcript_with_yt_dlp", return_value=transcript_segments) as mock_transcript, \
             patch("src.pipeline.transcript_to_text", return_value="ola"), \
             patch("src.pipeline.gerar_nota_md", return_value=tmp_path / "nota.md"), \
             patch("src.pipeline.salvar_transcricao"), \
             patch("src.pipeline.PROJECT_ROOT", tmp_path):

            youtube_to_notes(url="https://youtube.com/watch?v=cacheid")

        mock_transcript.assert_called_once()
