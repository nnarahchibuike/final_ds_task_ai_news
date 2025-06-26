"""
Configuration settings for DS Task AI News application.
"""
import os
from typing import List, Dict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("../.env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    cohere_api_key: str = os.getenv("COHERE_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")

    # Pinecone settings
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "news-articles")
    pinecone_namespace: str = os.getenv("PINECONE_NAMESPACE", "default")
    
    # Data directories
    raw_news_dir: str = os.getenv("RAW_NEWS_DIR", "./data/raw_news")
    processed_news_dir: str = os.getenv("PROCESSED_NEWS_DIR", "./data/processed_news")
    
    # RSS Feed URLs organized by category
    rss_feeds: Dict[str, List[str]] = {
        "mainstream_news": [
            "https://feeds.bbci.co.uk/news/rss.xml",
            "https://www.npr.org/rss/rss.php?id=1001",
            "https://www.theguardian.com/world/rss",
        ],
        "music": [
            "https://www.billboard.com/feed/",
            "https://pitchfork.com/rss/news/",
        ],
        "gaming": [
            "https://www.polygon.com/rss/index.xml",
            "https://kotaku.com/rss",
        ],
        "tech": [
            "https://www.theverge.com/rss/index.xml",
            "https://feeds.arstechnica.com/arstechnica/index",
        ],
        "lifestyle": [
            "https://lifehacker.com/rss",
            "https://www.buzzfeed.com/index.xml",
            "https://www.allrecipes.com/rss/daily-dish/",
        ]
    }
    
    # Embedding settings
    embedding_model: str = "embed-english-v3.0"
    embedding_dimension: int = 1024
    
    # LLM settings
    groq_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    max_tokens: int = 1000
    temperature: float = 0.7
    
    # News fetching settings
    fetch_interval_hours: int = 6
    max_articles_per_feed: int = 50
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # Recommendation settings
    max_recommendations: int = 10
    similarity_threshold: float = 0.25
    
    class Config:
        env_file = "../.env"  # Look for .env in parent directory
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
