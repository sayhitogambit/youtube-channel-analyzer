"""
YouTube Channel Analyzer Actor
"""

from .scraper import YouTubeAnalyzer
from .schema import (
    YouTubeAnalyzerInput,
    YouTubeAnalyzerOutput,
    ChannelInfo,
    YouTubeVideo,
    VideoComment
)

__version__ = "1.0.0"

__all__ = [
    'YouTubeAnalyzer',
    'YouTubeAnalyzerInput',
    'YouTubeAnalyzerOutput',
    'ChannelInfo',
    'YouTubeVideo',
    'VideoComment',
]
