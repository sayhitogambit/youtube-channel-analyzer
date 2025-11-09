"""
YouTube Channel Analyzer - Input/Output Schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator


class YouTubeAnalyzerInput(BaseModel):
    """Input schema for YouTube Channel Analyzer"""

    channel_url: Optional[HttpUrl] = Field(
        None,
        description="YouTube channel URL",
        example="https://www.youtube.com/@channelname"
    )

    channel_id: Optional[str] = Field(
        None,
        description="YouTube channel ID",
        example="UCxxxxxxxxxxxxxx"
    )

    max_videos: int = Field(
        30,
        ge=1,
        le=500,
        description="Maximum videos to analyze"
    )

    include_comments: bool = Field(
        False,
        description="Include comments for each video"
    )

    max_comments_per_video: int = Field(
        50,
        ge=0,
        le=200,
        description="Maximum comments per video"
    )

    date_from: Optional[str] = Field(
        None,
        description="Filter videos from date (YYYY-MM-DD)"
    )

    sort_by: str = Field(
        "newest",
        description="Sort videos by: newest, popular, oldest"
    )

    @validator('sort_by')
    def validate_sort_by(cls, v):
        valid_sorts = ['newest', 'popular', 'oldest']
        if v not in valid_sorts:
            raise ValueError(f"sort_by must be one of: {valid_sorts}")
        return v

    def model_post_init(self, __context):
        """Validate that either channel_url or channel_id is provided"""
        if not self.channel_url and not self.channel_id:
            raise ValueError("Either 'channel_url' or 'channel_id' must be provided")


class VideoComment(BaseModel):
    """YouTube comment schema"""
    comment_id: str
    author: str
    author_channel_url: Optional[str] = None
    text: str
    likes: int = 0
    published_at: str
    is_reply: bool = False


class YouTubeVideo(BaseModel):
    """YouTube video schema"""
    video_id: str
    title: str
    description: str
    published_at: str
    duration: str  # ISO 8601 format
    duration_seconds: int
    views: int
    likes: int
    comments_count: int
    thumbnail_url: str
    url: str
    tags: List[str] = []
    category: Optional[str] = None
    is_live: bool = False
    is_short: bool = False
    comments: List[VideoComment] = []


class ChannelInfo(BaseModel):
    """YouTube channel information schema"""
    channel_id: str
    channel_name: str
    channel_handle: Optional[str] = None
    description: str
    subscribers: int
    total_views: int
    video_count: int
    joined_date: Optional[str] = None
    country: Optional[str] = None
    custom_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    banner_url: Optional[str] = None
    keywords: List[str] = []


class YouTubeAnalyzerOutput(BaseModel):
    """Complete YouTube channel analysis output"""
    channel: ChannelInfo
    videos: List[YouTubeVideo]
    total_videos_analyzed: int
    average_views: float
    average_likes: float
    total_engagement: int

    class Config:
        json_schema_extra = {
            "example": {
                "channel": {
                    "channel_id": "UCxxxxxx",
                    "channel_name": "Example Channel",
                    "subscribers": 100000,
                    "total_views": 5000000,
                    "video_count": 250
                },
                "videos": [],
                "total_videos_analyzed": 30,
                "average_views": 10000.5,
                "average_likes": 500.2,
                "total_engagement": 15000
            }
        }
