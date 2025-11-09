# YouTube Channel Analyzer

Extract channel statistics, video metadata, and engagement metrics from any YouTube channel.

## Features

- ✅ **No API Key Required** - Scrapes data from YouTube's HTML
- 📊 **Channel Analytics** - Subscribers, views, video count
- 🎥 **Video Metadata** - Title, description, views, likes, duration
- 🔍 **Multiple Sort Options** - Newest, popular, or oldest videos
- 💬 **Comment Support** - Optional comment extraction (planned)
- 💾 **Smart Caching** - Avoid re-scraping same data
- 📈 **Engagement Metrics** - Calculate averages and totals
- 📊 **Multiple Export Formats** - JSON, CSV, Excel

## Installation

```bash
# Install dependencies
pip install -r ../../requirements.txt

# Copy environment template
cp ../../.env.example .env

# No special configuration needed
```

## Quick Start

### Run Examples

```bash
python main.py
```

Select from pre-configured examples or paste any YouTube channel URL.

### Basic Usage

```python
from scraper import YouTubeAnalyzer

# Initialize analyzer
analyzer = YouTubeAnalyzer(
    cache_config={'enabled': True, 'ttl': 3600},
    output_dir='output/youtube'
)

# Analyze channel
results = await analyzer.run({
    "channel_url": "https://www.youtube.com/@channelname",
    "max_videos": 30,
    "sort_by": "newest"
})
```

## Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `channel_url` | string (URL) | * | - | YouTube channel URL |
| `channel_id` | string | * | - | YouTube channel ID |
| `max_videos` | int | No | 30 | Max videos to analyze (1-500) |
| `include_comments` | bool | No | false | Include comments |
| `max_comments_per_video` | int | No | 50 | Max comments per video |
| `date_from` | string | No | - | Filter from date (YYYY-MM-DD) |
| `sort_by` | string | No | "newest" | Sort: newest, popular, oldest |

**Note:** Either `channel_url` or `channel_id` must be provided.

## Output Schema

### Channel Info

```json
{
  "channel_id": "UCxxxxxxxxxxxxxx",
  "channel_name": "Channel Name",
  "channel_handle": "@channelhandle",
  "description": "Channel description",
  "subscribers": 1000000,
  "total_views": 50000000,
  "video_count": 250,
  "joined_date": "2015-01-15",
  "country": "US",
  "thumbnail_url": "https://...",
  "keywords": ["tech", "tutorials"]
}
```

### Video Object

```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Video Title",
  "description": "Video description",
  "published_at": "2 days ago",
  "duration": "10:23",
  "duration_seconds": 623,
  "views": 1000000,
  "likes": 50000,
  "comments_count": 5000,
  "thumbnail_url": "https://...",
  "url": "https://www.youtube.com/watch?v=...",
  "tags": ["tech", "tutorial"],
  "category": "Education",
  "is_live": false,
  "is_short": false
}
```

### Complete Output

```json
{
  "channel": { ... },
  "videos": [ ... ],
  "total_videos_analyzed": 30,
  "average_views": 50000.5,
  "average_likes": 2500.2,
  "total_engagement": 75000
}
```

## Examples

### 1. Analyze Popular Videos

```python
input_data = {
    "channel_url": "https://www.youtube.com/@MrBeast",
    "max_videos": 50,
    "sort_by": "popular"
}

results = await analyzer.run(input_data)
```

### 2. Analyze by Channel ID

```python
input_data = {
    "channel_id": "UC8butISFwT-Wl7EV0hUK0BQ",  # freeCodeCamp
    "max_videos": 25,
    "sort_by": "newest"
}

results = await analyzer.run(input_data)
```

### 3. Get Oldest Videos

```python
input_data = {
    "channel_url": "https://www.youtube.com/@veritasium",
    "max_videos": 10,
    "sort_by": "oldest"
}

results = await analyzer.run(input_data)
```

## Finding Channel URLs

YouTube channels can have different URL formats:
```
https://www.youtube.com/@channelhandle
https://www.youtube.com/c/customname
https://www.youtube.com/channel/UCxxxxxxxxxxxxxx
```

All formats are supported. The analyzer will extract the channel ID automatically.

## Configuration

### Environment Variables

```bash
# Rate Limiting
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_WINDOW=60

# Caching
CACHE_ENABLED=true
CACHE_TTL=3600  # 1 hour

# Output
OUTPUT_DIR=output/youtube

# Proxies (optional)
PROXY_ENABLED=false
```

## Performance

- **Speed**: ~30 videos in 5-10 seconds
- **Rate Limit**: No strict limits, but be polite (30 req/min recommended)
- **Caching**: Channel/video data cached for 1 hour
- **No Authentication**: Public data only, no login required

## Best Practices

1. **Enable Caching**: Channel stats don't change frequently
2. **Reasonable Limits**: Don't scrape thousands of videos at once
3. **Respect Content**: Only public channels and videos
4. **Monitor Changes**: Track subscriber/view growth over time

## Limitations

- ❌ **No Private Channels** - Only public data accessible
- ❌ **No Exact Stats** - Some metrics are approximated (e.g., "1.2M")
- ❌ **Rate Limits** - YouTube may throttle excessive requests
- ❌ **Comment Extraction** - Not fully implemented yet
- ❌ **No API Access** - Relies on HTML scraping (may break if YouTube changes)

## Troubleshooting

### Could Not Extract Channel ID

- Verify the channel URL is correct
- Some very new channels may not work
- Try using the channel ID directly

### Missing Video Data

- YouTube may not load all videos at once
- Increase cache TTL for better reliability
- Some private/unlisted videos won't appear

### Parsing Errors

- YouTube occasionally changes HTML structure
- Check logs for specific errors
- May need to update selectors

## Output Files

Results exported to `output/youtube/`:

```
output/youtube/
├── youtubeanalyzer.json    # Full analysis data
├── youtubeanalyzer.csv     # Flattened data
└── youtubeanalyzer.xlsx    # Excel format (optional)
```

## Advanced Usage

### Track Channel Growth

```python
# First analysis
analysis_v1 = await analyzer.run({"channel_url": "..."})

# Wait some time (days/weeks)
analyzer.cache.enabled = False  # Disable cache
analysis_v2 = await analyzer.run({"channel_url": "..."})

# Compare
sub_growth = analysis_v2['channel']['subscribers'] - analysis_v1['channel']['subscribers']
print(f"Subscriber growth: +{sub_growth:,}")
```

### Find Best Performing Videos

```python
results = await analyzer.run({
    "channel_url": "https://www.youtube.com/@channel",
    "max_videos": 100,
    "sort_by": "popular"
})

top_10 = sorted(
    results[0]['videos'],
    key=lambda v: v['views'],
    reverse=True
)[:10]

for i, video in enumerate(top_10, 1):
    print(f"{i}. {video['title']} - {video['views']:,} views")
```

## Docker Deployment

```bash
# Build
docker build -t youtube-analyzer .

# Run
docker run -v $(pwd)/output:/app/output youtube-analyzer
```

## License

For educational purposes. Respect YouTube's Terms of Service.

---

**Happy Analyzing!** 📊
