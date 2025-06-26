"""
FastAPI main application for DS Task AI News.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import Optional
from loguru import logger

try:
    # Try absolute imports first (when run directly or from root)
    from config import get_settings
    from news_fetcher import get_news_fetcher
    from vector_store import get_vector_store
    from recommender import get_news_recommender
except ImportError:
    try:
        # Try relative imports (when run as module)
        from .config import get_settings
        from .news_fetcher import get_news_fetcher
        from .vector_store import get_vector_store
        from .recommender import get_news_recommender
    except ImportError:
        # Try backend.module imports (when imported from root directory)
        from backend.config import get_settings
        from backend.news_fetcher import get_news_fetcher
        from backend.vector_store import get_vector_store
        from backend.recommender import get_news_recommender

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI()



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
        articles = recommender.get_similar_articles(
            article_id=article_id,
            max_results=max_results
        )

        return {
            "articles": articles,
            "total_results": len(articles)
        }

    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"Error in recommend-news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def format_article_with_id(article: dict) -> dict:
    """Format article with consistent ID generation matching Pinecone logic."""
    import hashlib

    content_hash = hashlib.md5(
        f"{article.get('title', '')}{article.get('link', '')}".encode()
    ).hexdigest()
    article_id = f"{article.get('source_name', 'unknown')}_{content_hash}"

    return {
        "id": article_id,
        "title": article.get('title', ''),
        "content": article.get('content', ''),
        "date": article.get('published', ''),
        "link": article.get('link', ''),
        "source": article.get('source_url', ''),
        "categories": [article.get('category', 'general')],
        "summary": article.get('summary', '')
    }


async def save_to_vector_store(articles: list):
    """Background task to save articles to vector store."""
    try:
        logger.info("Starting background save to vector store")
        vector_store = get_vector_store()
        added_count = vector_store.add_articles(articles)
        logger.info(f"Successfully saved {added_count} articles to vector store")
    except Exception as e:
        logger.error(f"Error in background vector store save: {str(e)}")


@app.get("/fetch-news")
async def fetch_news(background_tasks: BackgroundTasks = BackgroundTasks()):
    """Fetch latest news from RSS feeds and return articles."""
    try:
        logger.info("News fetch requested")

        # Fetch articles immediately (fast operation)
        news_fetcher = get_news_fetcher()
        articles = news_fetcher.fetch_all_feeds()

        if articles:
            # Start background tasks for saving (slow operations)
            background_tasks.add_task(save_to_vector_store, articles)
            background_tasks.add_task(news_fetcher.save_raw_articles, articles)

            # Format articles with proper IDs for immediate return
            formatted_articles = [format_article_with_id(article) for article in articles]

            return {
                "status": "success",
                "articles": formatted_articles
            }
        else:
            return {
                "status": "success",
                "articles": []
            }

    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
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
