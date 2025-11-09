"""
YouTube Analyzer - Configuration
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables"""
    config = {
        # Proxy (optional for YouTube)
        'proxy': {
            'enabled': os.getenv('PROXY_ENABLED', 'false').lower() == 'true',
            'proxies': _parse_proxies(),
            'rotation_strategy': os.getenv('PROXY_ROTATION_STRATEGY', 'round_robin')
        },

        # Rate limiting (YouTube is lenient)
        'rate_limit': {
            'max_requests': int(os.getenv('RATE_LIMIT_REQUESTS', '30')),
            'time_window': int(os.getenv('RATE_LIMIT_WINDOW', '60'))
        },

        # Caching
        'cache': {
            'enabled': os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
            'cache_dir': os.getenv('CACHE_DIR', '.cache/youtube'),
            'ttl': int(os.getenv('CACHE_TTL', '3600'))  # 1 hour
        },

        # Output
        'output_dir': os.getenv('OUTPUT_DIR', 'output/youtube'),

        # Logging
        'log_level': os.getenv('LOG_LEVEL', 'INFO')
    }

    return config


def _parse_proxies():
    """Parse proxy configuration"""
    proxies = []

    proxy_server = os.getenv('PROXY_SERVER')
    if proxy_server:
        proxy_config = {'server': proxy_server}

        username = os.getenv('PROXY_USERNAME')
        password = os.getenv('PROXY_PASSWORD')

        if username and password:
            proxy_config['username'] = username
            proxy_config['password'] = password

        proxies.append(proxy_config)

    return proxies
