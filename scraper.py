"""
YouTube Channel Analyzer
Extract channel statistics, video metadata, and engagement metrics
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapling import Fetcher
from shared.base_actor import BaseActor
from shared.utils import retry_with_backoff
from schema import (
    YouTubeAnalyzerInput,
    YouTubeAnalyzerOutput,
    ChannelInfo,
    YouTubeVideo,
    VideoComment
)

logger = logging.getLogger(__name__)


class YouTubeAnalyzer(BaseActor):
    """
    YouTube Channel Analyzer

    Features:
        - Extract channel statistics and metadata
        - Analyze videos (views, likes, comments)
        - Optional comment extraction
        - Sort by newest, popular, or oldest
        - No API key required (scrapes HTML)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://www.youtube.com"

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input using Pydantic schema"""
        try:
            YouTubeAnalyzerInput(**input_data)
            return True
        except Exception as e:
            raise ValueError(f"Invalid input: {e}")

    async def scrape(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Main scraping method"""
        config = YouTubeAnalyzerInput(**input_data)

        logger.info(f"Starting YouTube analysis: {config.model_dump()}")

        # Extract channel ID if URL provided
        if config.channel_url:
            channel_id = await self._extract_channel_id(str(config.channel_url))
        else:
            channel_id = config.channel_id

        # Get channel info
        channel_info = await self._scrape_channel_info(channel_id)

        # Get videos
        videos = await self._scrape_videos(
            channel_id,
            config.max_videos,
            config.sort_by
        )

        # Scrape comments if requested
        if config.include_comments and videos:
            logger.info(f"Scraping comments for {len(videos)} videos...")
            videos = await self._scrape_comments_batch(
                videos,
                config.max_comments_per_video
            )

        # Calculate statistics
        total_views = sum(v.views for v in videos)
        total_likes = sum(v.likes for v in videos)
        avg_views = total_views / len(videos) if videos else 0
        avg_likes = total_likes / len(videos) if videos else 0

        # Create output
        output = YouTubeAnalyzerOutput(
            channel=channel_info,
            videos=videos,
            total_videos_analyzed=len(videos),
            average_views=round(avg_views, 2),
            average_likes=round(avg_likes, 2),
            total_engagement=total_likes + sum(v.comments_count for v in videos)
        )

        logger.info(f"Analyzed {len(videos)} videos from channel")

        # Return as dict (we'll return the full output structure)
        return [output.model_dump()]

    async def _extract_channel_id(self, channel_url: str) -> str:
        """
        Extract channel ID from channel URL

        Handles:
        - youtube.com/@handle
        - youtube.com/c/name
        - youtube.com/channel/ID
        """
        # If already a channel ID
        if channel_url.startswith('UC') and len(channel_url) == 24:
            return channel_url

        # Fetch the channel page to extract ID
        proxy = await self.get_proxy()

        # Fetcher is synchronous, not async
        try:
            fetcher = Fetcher(proxy=proxy)
            response = fetcher.get(channel_url)

            # Look for channel ID in page source
            match = re.search(r'"channelId":"(UC[\w-]{22})"', response.text)
            if match:
                channel_id = match.group(1)
                logger.info(f"Extracted channel ID: {channel_id}")
                return channel_id

            # Alternative pattern
            match = re.search(r'"externalId":"(UC[\w-]{22})"', response.text)
            if match:
                return match.group(1)

            raise ValueError(f"Could not extract channel ID from {channel_url}")

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    async def _scrape_channel_info(self, channel_id: str) -> ChannelInfo:
        """
        Scrape channel information

        Args:
            channel_id: YouTube channel ID

        Returns:
            ChannelInfo object
        """
        await self.rate_limit()

        url = f"{self.base_url}/channel/{channel_id}/about"

        proxy = await self.get_proxy()

        async with Fetcher(proxy=proxy)
                response = fetcher.get(url)

                # Extract JSON data embedded in page
                import json

                # Find ytInitialData
                match = re.search(r'var ytInitialData = ({.*?});', response.text)
                if not match:
                    raise ValueError("Could not find ytInitialData in page")

                data = json.loads(match.group(1))

                # Navigate to channel metadata
                header = data.get('header', {}).get('c4TabbedHeaderRenderer', {})
                metadata = data.get('metadata', {}).get('channelMetadataRenderer', {})

                # Extract subscriber count
                subscribers_text = header.get('subscriberCountText', {}).get('simpleText', '0')
                subscribers = self._parse_count(subscribers_text)

                # Video count from stats
                stats = header.get('videosCountText', {}).get('runs', [])
                video_count = 0
                if stats:
                    video_count = self._parse_count(stats[0].get('text', '0'))

                channel_info = ChannelInfo(
                    channel_id=channel_id,
                    channel_name=metadata.get('title', ''),
                    channel_handle=metadata.get('vanityChannelUrl', '').replace('/', ''),
                    description=metadata.get('description', ''),
                    subscribers=subscribers,
                    total_views=0,  # Not easily accessible without API
                    video_count=video_count,
                    country=metadata.get('country', None),
                    custom_url=metadata.get('vanityChannelUrl', None),
                    thumbnail_url=metadata.get('avatar', {}).get('thumbnails', [{}])[-1].get('url'),
                    keywords=metadata.get('keywords', '').split() if metadata.get('keywords') else []
                )

                if proxy and self.proxy_manager:
                    self.proxy_manager.report_success(proxy)

                return channel_info

            except Exception as e:
                if proxy and self.proxy_manager:
                    self.proxy_manager.report_failure(proxy)
                raise

    async def _scrape_videos(
        self,
        channel_id: str,
        max_videos: int,
        sort_by: str
    ) -> List[YouTubeVideo]:
        """
        Scrape videos from channel

        Args:
            channel_id: Channel ID
            max_videos: Maximum videos to scrape
            sort_by: Sort method

        Returns:
            List of YouTubeVideo objects
        """
        videos = []

        # Build URL based on sort
        if sort_by == 'popular':
            url = f"{self.base_url}/channel/{channel_id}/videos?view=0&sort=p&flow=grid"
        elif sort_by == 'oldest':
            url = f"{self.base_url}/channel/{channel_id}/videos?view=0&sort=da&flow=grid"
        else:  # newest
            url = f"{self.base_url}/channel/{channel_id}/videos?view=0&sort=dd&flow=grid"

        proxy = await self.get_proxy()

        async with Fetcher(proxy=proxy) as fetcher:
            response = fetcher.get(url)

            # Extract video data from ytInitialData
            import json
            match = re.search(r'var ytInitialData = ({.*?});', response.text)
            if not match:
                logger.warning("Could not find video data")
                return videos

            data = json.loads(match.group(1))

            # Navigate to video list
            tabs = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])

            video_items = []
            for tab in tabs:
                tab_renderer = tab.get('tabRenderer', {})
                if tab_renderer.get('selected'):
                    content = tab_renderer.get('content', {})
                    rich_grid = content.get('richGridRenderer', {}).get('contents', [])

                    for item in rich_grid:
                        video_renderer = item.get('richItemRenderer', {}).get('content', {}).get('videoRenderer', {})
                        if video_renderer:
                            video_items.append(video_renderer)

            # Parse videos
            for video_data in video_items[:max_videos]:
                try:
                    video = self._parse_video(video_data)
                    videos.append(video)
                except Exception as e:
                    logger.error(f"Error parsing video: {e}")
                    continue

        logger.info(f"Scraped {len(videos)} videos")
        return videos

    def _parse_video(self, data: Dict[str, Any]) -> YouTubeVideo:
        """Parse video data from YouTube's JSON structure"""
        video_id = data.get('videoId', '')

        title = data.get('title', {}).get('runs', [{}])[0].get('text', '')

        # Description
        description_snippets = data.get('descriptionSnippet', {}).get('runs', [])
        description = ' '.join([r.get('text', '') for r in description_snippets])

        # Published date
        published_text = data.get('publishedTimeText', {}).get('simpleText', '')

        # Duration
        duration_text = data.get('lengthText', {}).get('simpleText', '0:00')
        duration_seconds = self._parse_duration(duration_text)

        # View count
        view_count_text = data.get('viewCountText', {}).get('simpleText', '0 views')
        views = self._parse_count(view_count_text)

        # Thumbnail
        thumbnails = data.get('thumbnail', {}).get('thumbnails', [])
        thumbnail_url = thumbnails[-1].get('url', '') if thumbnails else ''

        return YouTubeVideo(
            video_id=video_id,
            title=title,
            description=description,
            published_at=published_text,
            duration=duration_text,
            duration_seconds=duration_seconds,
            views=views,
            likes=0,  # Not available in list view
            comments_count=0,  # Would need individual video page
            thumbnail_url=thumbnail_url,
            url=f"{self.base_url}/watch?v={video_id}",
            tags=[],
            category=None,
            is_live=data.get('badges', [{}])[0].get('metadataBadgeRenderer', {}).get('label', '') == 'LIVE',
            is_short=False
        )

    async def _scrape_comments_batch(
        self,
        videos: List[YouTubeVideo],
        max_comments: int
    ) -> List[YouTubeVideo]:
        """
        Scrape comments for multiple videos

        Note: This is a simplified version. Full comment scraping
        requires more complex handling of YouTube's comment system.
        """
        # For now, return videos as-is
        # Full implementation would require video page scraping
        logger.warning("Comment scraping not fully implemented yet")
        return videos

    def _parse_count(self, text: str) -> int:
        """
        Parse count from text like '1.2M', '15K', '1,234'

        Args:
            text: Count text

        Returns:
            Integer count
        """
        if not text:
            return 0

        # Remove non-numeric characters except K, M, B
        text = re.sub(r'[^\d.KMB]', '', text.upper())

        if not text:
            return 0

        multipliers = {
            'K': 1_000,
            'M': 1_000_000,
            'B': 1_000_000_000
        }

        for suffix, multiplier in multipliers.items():
            if suffix in text:
                number = float(text.replace(suffix, ''))
                return int(number * multiplier)

        # Try to parse as regular number
        try:
            return int(float(text))
        except:
            return 0

    def _parse_duration(self, duration_text: str) -> int:
        """
        Parse duration from text like '10:23' or '1:05:30'

        Args:
            duration_text: Duration string

        Returns:
            Duration in seconds
        """
        if not duration_text:
            return 0

        parts = duration_text.split(':')
        parts = [int(p) for p in parts]

        if len(parts) == 3:  # HH:MM:SS
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:  # MM:SS
            return parts[0] * 60 + parts[1]
        elif len(parts) == 1:  # SS
            return parts[0]

        return 0
