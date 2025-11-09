"""
YouTube Channel Analyzer - Main Entry Point
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scraper import YouTubeAnalyzer
from config import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""

    examples = {
        "1": {
            "name": "Analyze MrBeast channel",
            "input": {
                "channel_url": "https://www.youtube.com/@MrBeast",
                "max_videos": 30,
                "sort_by": "newest"
            }
        },
        "2": {
            "name": "Analyze Fireship (tech channel)",
            "input": {
                "channel_url": "https://www.youtube.com/@Fireship",
                "max_videos": 50,
                "sort_by": "popular"
            }
        },
        "3": {
            "name": "Analyze channel by ID",
            "input": {
                "channel_id": "UC8butISFwT-Wl7EV0hUK0BQ",  # freeCodeCamp
                "max_videos": 25,
                "sort_by": "newest"
            }
        },
        "4": {
            "name": "Get popular videos from a channel",
            "input": {
                "channel_url": "https://www.youtube.com/@veritasium",
                "max_videos": 20,
                "sort_by": "popular"
            }
        }
    }

    print("\n" + "="*60)
    print("YouTube Channel Analyzer")
    print("="*60)
    print("\nSelect an example to run:")
    for key, example in examples.items():
        print(f"  {key}. {example['name']}")
    print("  5. Custom input (modify main.py)")
    print("="*60)

    choice = input("\nEnter choice (1-5) or YouTube channel URL: ").strip()

    if choice in examples:
        input_data = examples[choice]["input"]
        print(f"\nRunning: {examples[choice]['name']}")
    elif 'youtube.com' in choice or 'youtu.be' in choice:
        # Direct URL input
        input_data = {
            "channel_url": choice,
            "max_videos": 30,
            "sort_by": "newest"
        }
        print(f"\nAnalyzing: {choice}")
    else:
        # Default
        input_data = {
            "channel_url": "https://www.youtube.com/@Fireship",
            "max_videos": 20,
            "sort_by": "popular"
        }
        print("\nRunning default: Fireship channel")

    print(f"Input: {input_data}\n")

    # Load configuration
    config = load_config()

    # Initialize scraper
    analyzer = YouTubeAnalyzer(
        proxy_config=config.get('proxy'),
        rate_limit=config.get('rate_limit'),
        cache_config=config.get('cache'),
        output_dir=config.get('output_dir', 'output/youtube')
    )

    try:
        # Run analyzer
        results = await analyzer.run(
            input_data=input_data,
            export_formats=['json', 'csv']
        )

        # Display results
        print("\n" + "="*60)
        print(f"✓ Analysis Complete!")
        print("="*60)

        if results:
            result = results[0]
            channel = result['channel']
            videos = result['videos']

            print(f"\nChannel Info:")
            print(f"  Name: {channel['channel_name']}")
            print(f"  ID: {channel['channel_id']}")
            print(f"  Subscribers: {channel['subscribers']:,}")
            print(f"  Total Videos: {channel['video_count']:,}")

            print(f"\nAnalysis Stats:")
            print(f"  Videos Analyzed: {result['total_videos_analyzed']}")
            print(f"  Average Views: {result['average_views']:,.0f}")
            print(f"  Average Likes: {result['average_likes']:,.0f}")
            print(f"  Total Engagement: {result['total_engagement']:,}")

            if videos:
                print(f"\nMost Recent Video:")
                video = videos[0]
                print(f"  Title: {video['title'][:70]}...")
                print(f"  Views: {video['views']:,}")
                print(f"  Duration: {video['duration']}")
                print(f"  URL: {video['url']}")

        # Stats
        stats = analyzer.get_stats()
        print(f"\nScraper Stats:")
        print(f"  Output directory: {stats['output_dir']}")

        if stats.get('cache_stats', {}).get('enabled'):
            cache_stats = stats['cache_stats']
            print(f"  Cache entries: {cache_stats.get('total_entries', 0)}")

        print("\n" + "="*60)
        print("Analysis completed successfully!")
        print("="*60 + "\n")

    except Exception as e:
        logger.error(f"Error running analyzer: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
