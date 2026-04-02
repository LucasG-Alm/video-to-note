import pytest
from unittest.mock import patch
from src.services.notebooklm_cli import NotebookLMClient


def test_notebooklm_client_init():
    """Client initializes with notebook_id."""
    client = NotebookLMClient("nb-123")
    assert client.notebook_id == "nb-123"


def test_add_youtube_source():
    """add_youtube_source parses CLI output."""
    with patch('src.services.notebooklm_cli.run_notebooklm') as mock_run:
        mock_run.return_value = {
            'source_id': 'src-abc',
            'title': 'Video Title',
            'status': 'processing'
        }

        client = NotebookLMClient("nb-123")
        result = client.add_youtube_source("https://youtube.com/watch?v=abc")

        assert result['source_id'] == 'src-abc'
        assert result['title'] == 'Video Title'


def test_summarize_chapter():
    """summarize_chapter returns answer from CLI."""
    with patch('src.services.notebooklm_cli.run_notebooklm') as mock_run:
        mock_run.return_value = {'answer': 'Chapter summary text...'}

        client = NotebookLMClient("nb-123")
        summary = client.summarize_chapter("Intro", 0, 300)

        assert summary == 'Chapter summary text...'


def test_remove_source():
    """remove_source calls CLI delete."""
    with patch('src.services.notebooklm_cli.run_notebooklm') as mock_run:
        mock_run.return_value = "Deleted"

        client = NotebookLMClient("nb-123")
        result = client.remove_source("src-abc")

        assert result is True


def test_add_youtube_source_handles_error():
    """add_youtube_source returns None dict on CLI failure."""
    with patch('src.services.notebooklm_cli.run_notebooklm') as mock_run:
        mock_run.return_value = None  # CLI failed

        client = NotebookLMClient("nb-123")
        result = client.add_youtube_source("https://youtube.com/watch?v=abc")

        assert result['source_id'] is None


def test_summarize_chapter_empty_on_error():
    """summarize_chapter returns empty string on CLI failure."""
    with patch('src.services.notebooklm_cli.run_notebooklm') as mock_run:
        mock_run.return_value = None  # CLI failed

        client = NotebookLMClient("nb-123")
        summary = client.summarize_chapter("Intro")

        assert summary == ""


def test_wait_for_source():
    """wait_for_source returns True on success."""
    with patch('src.services.notebooklm_cli.run_notebooklm') as mock_run:
        mock_run.return_value = "Ready"

        client = NotebookLMClient("nb-123")
        result = client.wait_for_source("src-123")

        assert result is True
