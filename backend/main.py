"""
FastAPI main application for DS Task AI News.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

try:
    # Try absolute imports first (when run directly or from root)
    from config import get_settings
    from vector_store import get_vector_store
    from recommender import get_news_recommender
except ImportError:
    try:
        # Try relative imports (when run as module)
        from .config import get_settings
        from .vector_store import get_vector_store
        from .recommender import get_news_recommender
    except ImportError:
        # Try backend.module imports (when imported from root directory)
        from backend.config import get_settings
        from backend.vector_store import get_vector_store
        from backend.recommender import get_news_recommender

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(title="AI News Hub", description="AI-powered news aggregation and recommendation system")

# Setup static files serving for frontend
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
    logger.info(f"Frontend static files mounted from: {frontend_dir}")
else:
    logger.warning(f"Frontend directory not found at: {frontend_dir}")

@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html at the root path."""
    frontend_file = frontend_dir / "index.html"
    if frontend_file.exists():
        return FileResponse(str(frontend_file))
    else:
        return {"message": "AI News Hub API", "docs": "/docs", "frontend": "Frontend not found"}



@app.get("/recommend-news")
async def recommend_news(article_id: str, max_results: Optional[int] = None):
    """
    Get news recommendations based on an existing article ID.

    Args:
        article_id: Required query parameter for the source article ID
        max_results: Optional query parameter for number of recommendations

    Returns:
        JSON with similar articles
    """
    try:
        logger.info(f"Recommendation request for article ID: {article_id}")

        # Get the recommender
        recommender = get_news_recommender()
        vector_store = get_vector_store()

        # First, get the source article to create a meaningful query description
        source_article = vector_store.get_article_by_id(article_id)
        if not source_article:
            logger.warning(f"Article with ID {article_id} not found")
            raise HTTPException(status_code=404, detail=f"Article with ID '{article_id}' not found")

        # Get similar articles
        raw_articles = recommender.get_similar_articles(
            article_id=article_id,
            max_results=max_results
        )

        # Format articles to match the expected frontend structure
        formatted_articles = []
        for article in raw_articles:
            formatted_article = {
                "id": article.get('id', ''),
                "title": article.get('title', ''),
                "content": article.get('content_preview', ''),
                "date": article.get('published', ''),  # Map 'published' to 'date'
                "url": article.get('link', ''),
                "source": article.get('source_name', ''),
                "categories": [article.get('category', 'general')],
                "tags": article.get('tags', []),  # Now includes tags from vector store metadata
                "summary": article.get('summary', ''),
                "author": '',
                "slug": '',
                "similarity_score": article.get('similarity_score', 0)
            }
            formatted_articles.append(formatted_article)

        return {
            "articles": formatted_articles,
            "total_results": len(formatted_articles)
        }

    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"Error in recommend-news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def format_article_with_id(article: dict) -> dict:
    """Format article with uniform ID generation using MD5 hash."""
    import hashlib
    import re

    # Generate uniform ID: {source_name}_{md5_hash}
    content_hash = hashlib.md5(
        f"{article.get('title', '')}{article.get('url', article.get('link', ''))}".encode()
    ).hexdigest()

    # Extract and clean source name
    source_feed = article.get('source_feed', article.get('source_url', 'unknown'))
    source_name = source_feed.split('/')[-1].replace('.xml', '').replace('.rss', '').replace('.', '_')
    source_name = re.sub(r'[^a-zA-Z0-9_]', '_', source_name)

    article_id = f"{source_name}_{content_hash}"

    return {
        "id": article_id,
        "title": article.get('title', ''),
        "content": article.get('content', ''),
        "date": article.get('date', article.get('published', '')),
        "url": article.get('url', article.get('link', '')),
        "source": article.get('source_feed', article.get('source_url', '')),
        "categories": article.get('categories', [article.get('category', 'general')] if article.get('category') else []),
        "tags": article.get('tags', []),
        "summary": article.get('summary', ''),
        "author": article.get('author', ''),
        "slug": article.get('slug', '')
    }


def get_latest_processed_articles() -> tuple[list, dict]:
    """
    Load the latest processed articles from the pipeline output.

    Looks for the most recent processed file in the data/processed_news directory.
    Supports both timestamped files (processed_news_YYYYMMDD_HHMMSS.json)
    and the legacy latest_articles.json format.

    Returns:
        Tuple of (articles_list, metadata_dict)
    """
    import json
    import glob
    from pathlib import Path

    processed_dir = Path(settings.processed_news_dir)

    # First, try to find timestamped processed files
    processed_pattern = str(processed_dir / "processed_news_*.json")
    processed_files = glob.glob(processed_pattern)

    # Also check for API articles files
    api_pattern = str(processed_dir / "api_articles_*.json")
    api_files = glob.glob(api_pattern)

    # Combine all processed files
    all_files = processed_files + api_files

    # Fallback to legacy latest_articles.json if no timestamped files found
    legacy_file = processed_dir / "latest_articles.json"
    if not all_files and legacy_file.exists():
        all_files = [str(legacy_file)]

    if not all_files:
        logger.warning("No processed articles found. Please run the pipeline first: python pipeline.py")
        return [], {"error": "No processed articles available", "last_processed": None}

    # Sort files by modification time (most recent first)
    all_files.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
    latest_file = Path(all_files[0])

    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)

        # Get file modification time for metadata
        last_modified = latest_file.stat().st_mtime
        last_processed = datetime.fromtimestamp(last_modified).isoformat()

        metadata = {
            "total_articles": len(articles),
            "last_processed": last_processed,
            "source_file": str(latest_file),
            "pipeline_required": False,
            "available_files": len(all_files)
        }

        logger.info(f"Loaded {len(articles)} processed articles from {latest_file}")
        return articles, metadata

    except Exception as e:
        logger.error(f"Error loading processed articles: {str(e)}")
        return [], {"error": str(e), "last_processed": None}


@app.get("/fetch-news")
async def fetch_news():
    """
    Fetch latest processed news articles from the pipeline output.

    This endpoint now reads from pre-processed files created by the standalone pipeline.
    To get fresh articles, run: python pipeline.py
    """
    try:
        logger.info("News fetch requested - loading from processed files")

        # Load processed articles from pipeline output
        articles, metadata = get_latest_processed_articles()

        if metadata.get("error"):
            raise HTTPException(
                status_code=404,
                detail=f"No processed articles available. {metadata['error']}. Please run the pipeline first: python pipeline.py"
            )

        return {
            "status": "success",
            "message": f"Loaded {len(articles)} processed articles",
            "total_articles": len(articles),
            "last_processed": metadata.get("last_processed"),
            "articles": articles[:50],  # Return first 50 for preview
            "metadata": {
                "total_available": len(articles),
                "last_pipeline_run": metadata.get("last_processed"),
                "data_source": "pre-processed",
                "note": "To refresh articles, run: python pipeline.py"
            }
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in fetch-news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.api_host}:{settings.api_port}")
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
