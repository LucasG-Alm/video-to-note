"""Utilities for detecting video length thresholds."""

LONG_VIDEO_THRESHOLD_SECONDS = 30 * 60  # 30 minutes

def is_long_video(duration_seconds: int | float | None) -> bool:
    """True if duration > 30 min."""
    if not duration_seconds:
        return False
    return duration_seconds > LONG_VIDEO_THRESHOLD_SECONDS
