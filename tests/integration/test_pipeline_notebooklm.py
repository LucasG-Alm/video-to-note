"""Integration tests for NotebookLM chapter summarization in pipeline."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.pipeline import youtube_to_notes


def test_youtube_to_notes_uses_notebooklm_for_long_video_with_chapters():
    """Long video with chapters uses NotebookLM summarization."""
    with patch('src.pipeline.get_video_metadata') as mock_meta, \
         patch('src.pipeline.NotebookLMClient') as mock_nlm_cls, \
         patch('src.pipeline.is_long_video', return_value=True), \
         patch('src.pipeline.gerar_nota_md') as mock_gerar, \
         patch('src.pipeline.get_transcript_with_yt_dlp', return_value=None), \
         patch('src.pipeline.salvar_transcricao'), \
         patch('src.pipeline.extract_video_id', return_value='abc123'), \
         patch('src.pipeline.get_config') as mock_config:

        # Setup metadata
        mock_meta.return_value = {
            'title': 'Long Video with Chapters',
            'duration_sec': 3600,
            'chapters': [
                {'title': 'Intro', 'start_time': 0, 'end_time': 300},
                {'title': 'Main Content', 'start_time': 300, 'end_time': 3000},
            ]
        }

        # Setup config
        mock_config_instance = mock_config.return_value
        mock_config_instance.get.side_effect = lambda key: {
            'NOTEBOOKLM_NOTEBOOK_ID': 'nb-123',
            'NOTEBOOKLM_LAST_SOURCE_ID': None,
        }.get(key)

        # Setup NotebookLM client
        mock_nlm = mock_nlm_cls.return_value
        mock_nlm.add_youtube_source.return_value = {
            'source_id': 'src-1',
            'title': 'Long Video with Chapters',
            'status': 'processing'
        }
        mock_nlm.wait_for_source.return_value = True
        mock_nlm.summarize_chapter.side_effect = [
            "Summary of intro section with key points.",
            "Summary of main content section with detailed insights.",
        ]

        # Setup note generation
        mock_gerar.return_value = Path('note.md')

        # Execute
        result = youtube_to_notes(
            'https://youtube.com/watch?v=abc123',
            depth='intermediario'
        )

        # Verify NotebookLM was used
        assert mock_nlm_cls.called
        assert mock_nlm.add_youtube_source.called
        assert mock_nlm.wait_for_source.called
        assert mock_nlm.summarize_chapter.call_count == 2
        assert result == Path('note.md')


def test_youtube_to_notes_falls_back_to_groq_on_notebooklm_failure():
    """Falls back to Groq when NotebookLM fails."""
    with patch('src.pipeline.get_video_metadata') as mock_meta, \
         patch('src.pipeline.NotebookLMClient') as mock_nlm_cls, \
         patch('src.pipeline.is_long_video', return_value=True), \
         patch('src.pipeline.gerar_nota_md') as mock_gerar, \
         patch('src.pipeline.get_transcript_with_yt_dlp', return_value={'text': 'transcript'}), \
         patch('src.pipeline.transcript_to_text', return_value='transcript text'), \
         patch('src.pipeline.salvar_transcricao'), \
         patch('src.pipeline.extract_video_id', return_value='abc123'), \
         patch('src.pipeline.get_config') as mock_config:

        # Setup metadata
        mock_meta.return_value = {
            'title': 'Long Video',
            'duration_sec': 3600,
            'chapters': [
                {'title': 'Intro', 'start_time': 0, 'end_time': 300},
            ]
        }

        # Setup config with no notebook ID (NotebookLM not configured)
        mock_config_instance = mock_config.return_value
        mock_config_instance.get.side_effect = lambda key: {
            'NOTEBOOKLM_NOTEBOOK_ID': None,  # Not configured
        }.get(key)

        # Setup note generation
        mock_gerar.return_value = Path('note.md')

        # Execute
        result = youtube_to_notes(
            'https://youtube.com/watch?v=abc123',
            depth='intermediario'
        )

        # Verify Groq pipeline was used instead
        assert mock_gerar.called
        assert result == Path('note.md')


def test_youtube_to_notes_skips_notebooklm_for_short_videos():
    """Short videos (< 30 min) skip NotebookLM and use Groq."""
    with patch('src.pipeline.get_video_metadata') as mock_meta, \
         patch('src.pipeline.NotebookLMClient') as mock_nlm_cls, \
         patch('src.pipeline.is_long_video', return_value=False), \
         patch('src.pipeline.gerar_nota_md') as mock_gerar, \
         patch('src.pipeline.get_transcript_with_yt_dlp', return_value={'text': 'transcript'}), \
         patch('src.pipeline.transcript_to_text', return_value='transcript text'), \
         patch('src.pipeline.salvar_transcricao'), \
         patch('src.pipeline.extract_video_id', return_value='abc123'):

        # Setup metadata for short video
        mock_meta.return_value = {
            'title': 'Short Video',
            'duration_sec': 600,  # 10 minutes
            'chapters': []
        }

        # Setup note generation
        mock_gerar.return_value = Path('note.md')

        # Execute
        result = youtube_to_notes(
            'https://youtube.com/watch?v=abc123',
            depth='intermediario'
        )

        # Verify NotebookLM was NOT used
        assert not mock_nlm_cls.called
        assert mock_gerar.called
        assert result == Path('note.md')


def test_youtube_to_notes_skips_notebooklm_without_chapters():
    """Long videos without chapters skip NotebookLM and use Groq."""
    with patch('src.pipeline.get_video_metadata') as mock_meta, \
         patch('src.pipeline.NotebookLMClient') as mock_nlm_cls, \
         patch('src.pipeline.is_long_video', return_value=True), \
         patch('src.pipeline.gerar_nota_md') as mock_gerar, \
         patch('src.pipeline.get_transcript_with_yt_dlp', return_value={'text': 'transcript'}), \
         patch('src.pipeline.transcript_to_text', return_value='transcript text'), \
         patch('src.pipeline.salvar_transcricao'), \
         patch('src.pipeline.extract_video_id', return_value='abc123'):

        # Setup metadata for long video WITHOUT chapters
        mock_meta.return_value = {
            'title': 'Long Video No Chapters',
            'duration_sec': 3600,
            'chapters': []  # No chapters
        }

        # Setup note generation
        mock_gerar.return_value = Path('note.md')

        # Execute
        result = youtube_to_notes(
            'https://youtube.com/watch?v=abc123',
            depth='intermediario'
        )

        # Verify NotebookLM was NOT used
        assert not mock_nlm_cls.called
        assert mock_gerar.called
        assert result == Path('note.md')
