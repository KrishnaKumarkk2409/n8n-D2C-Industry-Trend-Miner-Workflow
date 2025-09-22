# Custom ETL of D2C Trend Fetcher [fastapi]

A FastAPI-based web service that aggregates trending content related to Direct-to-Consumer (D2C) ecommerce from multiple sources including news feeds, social media, developer platforms, and market data.

## Quick Start

Run this in the downloaded Repo
```bash
bash run.sh
```

## Features

- **Multi-source Data Aggregation**: Fetches trending D2C content from 15+ sources
- **Intelligent Parsing**: Handles JSON, XML/RSS, HTML, and Atom feeds
- **Sentiment Analysis**: Basic headline sentiment scoring
- **Concurrent Processing**: Configurable concurrent requests for optimal performance
- **Data Normalization**: Standardizes data format across all sources
- **Deduplication**: Removes duplicate articles based on URLs
- **HTTP/2 Support**: Optional HTTP/2 support for better performance

## Requirements

### Python Dependencies

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
beautifulsoup4>=4.12.0
feedparser>=6.0.0
h2>=4.1.0
```

### System Requirements

- Python 3.8+
- Internet connection for fetching external data sources

### Optional Dependencies

- `h2` - For HTTP/2 support (recommended for better performance)

## Installation

1. **Clone or download the application**:
```bash
# Save the app.py file to your project directory
```

2. **Install dependencies**:
```bash
pip install fastapi uvicorn httpx beautifulsoup4 feedparser h2
```

3. **Run the application**:
```bash
python app.py
```

Or using uvicorn directly:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HTTP_TIMEOUT` | `15` | HTTP request timeout in seconds |
| `MAX_CONCURRENCY` | `8` | Maximum concurrent requests |
| `PORT` | `8000` | Server port |

Example:
```bash
export HTTP_TIMEOUT=20
export MAX_CONCURRENCY=12
export PORT=8080
python app.py
```

## Data Sources

The application aggregates data from these sources:

### News & Media
- **Google News RSS**: D2C and ecommerce news (India region)
- **GDELT Project**: Global news events and articles
- **YouTube**: D2C India ecommerce content

### Social Media
- **Reddit**: r/IndiaStartups and r/ecommerce subreddits
- **Hacker News**: Tech discussions via Algolia API

### Market Data
- **Google Trends**: Daily trending searches (India)
- **Yahoo Finance**: Trending stock tickers (India)
- **Apple App Store**: Top free and grossing apps (Shopping category)

### Developer Platforms
- **GitHub**: Repository search for ecommerce/D2C projects
- **npm Registry**: JavaScript packages related to ecommerce

### Knowledge & Research
- **OpenAlex**: Academic research papers
- **Wikipedia**: Page view analytics for D2C topics
- **Amazon India**: Movers & Shakers products

## API Endpoints

### Health Check
Check service status and configuration.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "ok": true,
  "ts": "2025-09-22T10:30:45.123456+00:00",
  "http2": true
}
```

### List Sources
Get all configured data sources.

**Endpoint**: `GET /sources`

**Parameters**:
- `file` (optional): Path to external URLs JSON file

**Response**:
```json
[
  {
    "source": "Google News RSS (Search)",
    "category": "news",
    "endpoint": "https://news.google.com/rss/search?q=...",
    "method": "GET",
    "format": "xml",
    "region": "IN",
    "auth_required": false
  }
]
```

### Aggregated Feed
Get normalized, deduplicated articles from all sources.

**Endpoint**: `GET /feed`

**Parameters**:
- `file` (optional): Path to external URLs JSON file
- `limit_per_source` (default: 50): Max items per source (1-200)
- `concurrent` (default: 8): Concurrent requests (1-32)
- `require_published` (default: true): Only include items with publication dates

**Response**:
```json
{
  "fetched_at": "2025-09-22T10:30:45.123456+00:00",
  "count": 245,
  "items": [
    {
      "title": "New D2C Brand Raises $10M Series A",
      "source": {"name": "example.com"},
      "author": "John Doe",
      "url": "https://example.com/article",
      "publishedAt": "2025-09-22T09:15:30+00:00",
      "description": "Article summary...",
      "urlToImage": "https://example.com/image.jpg",
      "content": "Full article content...",
      "language": "en",
      "documentSentiment": {
        "magnitude": 2.0,
        "score": 0.75
      }
    }
  ]
}
```

### Raw Trends Data
Get raw, unprocessed data from all sources for debugging.

**Endpoint**: `GET /trends`

**Parameters**:
- `file` (optional): Path to external URLs JSON file
- `limit_per_source` (default: 20): Max items per source (0-200)
- `concurrent` (default: 8): Concurrent requests (1-32)

## cURL Examples

### Basic Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

### Get All Sources
```bash
curl -X GET "http://localhost:8000/sources"
```

### Get Latest D2C Feed (Default Settings)
```bash
curl -X GET "http://localhost:8000/feed"
```

### Get Feed with Custom Parameters
```bash
curl -X GET "http://localhost:8000/feed?limit_per_source=25&concurrent=12&require_published=false"
```

### Get Raw Trends Data
```bash
curl -X GET "http://localhost:8000/trends"
```

### Get Trends with Debugging (More Items)
```bash
curl -X GET "http://localhost:8000/trends?limit_per_source=100&concurrent=16"
```

### Using External Configuration File
```bash
curl -X GET "http://localhost:8000/feed?file=/path/to/custom/urls.json"
```

### Save Response to File
```bash
curl -X GET "http://localhost:8000/feed" -o d2c_trends.json
```

### Pretty Print JSON Response
```bash
curl -X GET "http://localhost:8000/feed" | python -m json.tool
```

### Get Feed with Specific Limits and Save
```bash
curl -X GET "http://localhost:8000/feed?limit_per_source=30&concurrent=10" \
  -H "Accept: application/json" \
  -o "d2c_feed_$(date +%Y%m%d_%H%M%S).json"
```

### Check API with Timeout
```bash
curl -X GET "http://localhost:8000/feed" --max-time 60
```

## Custom Source Configuration

You can provide a custom `urls.json` file with additional sources:

```json
[
  {
    "source": "Custom News Feed",
    "category": "news",
    "endpoint": "https://example.com/rss",
    "method": "GET",
    "format": "xml",
    "region": "Global",
    "auth_required": false,
    "notes": "Custom RSS feed for D2C news"
  }
]
```

## Response Data Schema

### Normalized Article Object
```json
{
  "title": "string",
  "source": {"name": "string"},
  "author": "string|null",
  "url": "string",
  "publishedAt": "string|null (ISO 8601)",
  "description": "string|null",
  "urlToImage": "string|null",
  "content": "string|null",
  "language": "string",
  "documentSentiment": {
    "magnitude": "number",
    "score": "number (-1 to 1)"
  }
}
```

### Sentiment Scoring
- **Magnitude**: Number of sentiment-bearing words found
- **Score**: -1 (negative) to +1 (positive)
  - Based on keywords: "rise", "growth", "record" (positive) vs "decline", "fall", "loss" (negative)

## Error Handling

The API handles various error conditions gracefully:
- Network timeouts and connection errors
- Invalid JSON/XML responses
- Rate limiting from external APIs
- Missing or malformed data

Failed sources will return error information in `/trends` endpoint but won't break the overall aggregation.

## Performance Notes

- Default concurrency is set to 8 for balanced performance
- HTTP/2 support improves connection reuse
- Responses are deduplicated by URL
- Large responses are automatically truncated for memory efficiency

## License

This code appears to be a custom implementation. Check with the original author for licensing terms.

MIT License

Copyright (c) 2025 Krishna Kumar <a href= 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

```bash

D2C Trend Fetcher API

Copyright (c) 2025 Krishna Kumar. All rights reserved.
Licensed under MIT License 

Author: Krishna Kumar
Email: krishnakumar.kk2409@gmail.com
Version: 1.0.0

```

## Development

To run in development mode with auto-reload:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

For production deployment, consider using:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```


OR
## Quick Start

Run this in the downloaded Repo
```bash
bash run.sh
```