import pytest
from src.utils.duration_utils import is_long_video

def test_is_long_video_threshold_30_minutes():
    """Videos > 30 minutes marked as long."""
    assert is_long_video(1801) is True   # 30min 1sec
    assert is_long_video(1800) is False  # exactly 30min
    assert is_long_video(900) is False   # 15min
    assert is_long_video(0) is False
    assert is_long_video(None) is False
