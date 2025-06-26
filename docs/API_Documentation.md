# DS Task AI News - API Documentation

## Overview

The DS Task AI News API is a backend-only service that provides intelligent news aggregation and recommendation capabilities. It fetches news from RSS feeds, stores them in a vector database, and provides AI-powered recommendations based on article similarity.

## Base URL

```
http://localhost:8000
```

## Authentication

The API does not require authentication for endpoints. However, you must configure the following API keys in your environment:

- `COHERE_API_KEY` - For generating embeddings
- `GROQ_API_KEY` - For LLM operations (optional)
- `PINECONE_API_KEY` - For vector database operations

## Endpoints

### 1. Fetch News

**GET** `/fetch-news`

Fetches the latest news articles from all configured RSS feeds and returns them immediately. Articles are also saved to the vector database in the background.

**Query Parameters:** None

**Response:**

```json
{
  "status": "success",
  "articles": [
    {
      "id": "bbc_a1b2c3d4e5f6",
      "title": "Breaking News: Major Development in Technology",
      "content": "Full article content...",
      "date": "2024-01-01T12:00:00",
      "link": "https://example.com/article",
      "source": "https://feeds.bbci.co.uk/news/rss.xml",
      "categories": ["general"],
      "summary": "Article summary..."
    }
  ]
}
```

**Example:**

```bash
curl -X GET "http://localhost:8000/fetch-news"
```

### 2. Get News Recommendations

**GET** `/recommend-news`

Returns news articles similar to a given article based on vector similarity search.

**Query Parameters:**

- `article_id` (required): The ID of the source article to base recommendations on
- `max_results` (optional): Maximum number of recommendations to return (default: 10)

**Response:**

```json
{
  "articles": [
    {
      "id": "cnn_x1y2z3a4b5c6",
      "title": "Related Article Title",
      "content": "Article content...",
      "date": "2024-01-01T11:30:00",
      "link": "https://example.com/related-article",
      "source": "https://rss.cnn.com/rss/edition.rss",
      "categories": ["general"],
      "summary": "Related article summary..."
    }
  ],
  "total_results": 5
}
```

**Example:**

```bash
curl -X GET "http://localhost:8000/recommend-news?article_id=bbc_a1b2c3d4e5f6&max_results=5"
```

### 3. Interactive Documentation

**GET** `/docs`

Access the interactive API documentation (Swagger UI) for testing endpoints directly in your browser.

**GET** `/redoc`

Access alternative API documentation with a clean, readable interface.

## Response Schemas

### Article Object

```json
{
  "id": "string",           // Unique article identifier (source_hash)
  "title": "string",        // Article title
  "content": "string",      // Full article content
  "date": "string",         // Publication date (ISO format)
  "link": "string",         // Original article URL
  "source": "string",       // RSS feed URL
  "categories": ["string"], // Article categories
  "summary": "string"       // Article summary
}
```

## Error Responses

All endpoints return standard HTTP status codes with JSON error responses:

```json
{
  "detail": "Error description"
}
```

**Common Status Codes:**

- `200` - Success
- `404` - Article not found (for recommendations)
- `422` - Validation error (missing required parameters)
- `500` - Internal server error

## Configuration

The API behavior can be configured through environment variables:

### RSS Feeds

News sources are configured in `backend/config.py` with feeds organized by category:

- **Mainstream News**: BBC, NPR, The Guardian, Reuters
- **Music**: Billboard, Rolling Stone, Pitchfork
- **Gaming**: IGN, GameSpot, Polygon
- **Tech**: The Verge, TechCrunch, Ars Technica
- **Lifestyle**: Vogue, GQ, Elle

### Vector Database Settings

- `PINECONE_INDEX_NAME` - Pinecone index name (default: "news-articles")
- `PINECONE_NAMESPACE` - Pinecone namespace (default: "default")
- `EMBEDDING_DIMENSION` - Vector dimension (default: 1024)

### Processing Settings

- `MAX_ARTICLES_PER_FEED` - Maximum articles per RSS feed (default: 50)
- `MAX_RECOMMENDATIONS` - Maximum recommendations returned (default: 10)
- `SIMILARITY_THRESHOLD` - Minimum similarity score (default: 0.25)

## Usage Examples

### Basic Workflow

1. **Fetch latest news:**
   ```bash
   curl -X GET "http://localhost:8000/fetch-news"
   ```

2. **Get article ID from response and find similar articles:**
   ```bash
   curl -X GET "http://localhost:8000/recommend-news?article_id=bbc_a1b2c3d4e5f6"
   ```

### Integration Example (Python)

```python
import requests

# Fetch news
response = requests.get("http://localhost:8000/fetch-news")
articles = response.json()["articles"]

# Get recommendations for first article
if articles:
    article_id = articles[0]["id"]
    recommendations = requests.get(
        f"http://localhost:8000/recommend-news?article_id={article_id}&max_results=3"
    )
    similar_articles = recommendations.json()["articles"]
```

## Development

### Testing the API

Use the interactive documentation at `http://localhost:8000/docs` to test endpoints directly in your browser.

### Adding New RSS Feeds

Edit `backend/config.py` and add feeds to the appropriate category in the `rss_feeds` dictionary.

### Debugging

Use `backend/debug_rss.py` to test RSS feed parsing and troubleshoot feed issues.

## Deployment

The API is production-ready and can be deployed using any ASGI server:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

For containerized deployment, ensure all environment variables are properly configured.
