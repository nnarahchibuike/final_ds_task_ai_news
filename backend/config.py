"""
Configuration settings for DS Task AI News application.
"""
import os
from typing import List, Dict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("./.env")


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
    raw_news_dir: str = os.getenv("RAW_NEWS_DIR", "data/raw_news")
    processed_news_dir: str = os.getenv("PROCESSED_NEWS_DIR", "data/processed_news")
    
    # RSS Feed URLs organized by category
    rss_feeds: Dict[str, List[str]] = {
        "general": [
            "https://kotaku.com/rss",
            "https://pitchfork.com/rss/news/",
            "https://www.allrecipes.com/rss/daily-dish/",
        ]

    }
    
    # Embedding settings
    embedding_model: str = "embed-english-v3.0"
    embedding_dimension: int = 1024

    # Cohere API rate limiting (for trial accounts)
    cohere_batch_size: int = int(os.getenv("COHERE_BATCH_SIZE", "10"))
    cohere_rate_limit_delay: float = float(os.getenv("COHERE_RATE_LIMIT_DELAY", "6.0"))
    
    # LLM settings
    groq_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    max_tokens: int = 1000
    temperature: float = 0.7

    # News processing settings
    summary_min_words: int = 175  # Consistent summary length
    summary_max_words: int = 175  # Consistent summary length (same as min for uniformity)
    processing_batch_size: int = 10
    groq_rate_limit_delay: float = 2.0  # seconds between API calls (30 calls per minute = 2 seconds)
    content_cleaning_enabled: bool = True

    # Groq batch processing settings
    groq_batch_size: int = 15  # Number of articles to process in one API call
    groq_max_tokens_per_request: int = 25000  # Conservative limit for 30k token capacity
    groq_max_content_length_per_article: int = 1500  # Max content length per article for batching

    # News fetching settings
    fetch_interval_hours: int = 6
    max_articles_per_feed: int = 50
    deduplication_enabled: bool = True
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # Recommendation settings
    max_recommendations: int = 10
    similarity_threshold: float = 0.25

    # Pipeline settings
    pipeline_mode: bool = False  # True when running standalone pipeline
    skip_vector_operations: bool = os.getenv("SKIP_VECTOR_OPERATIONS", "false").lower() == "true"
    cleanup_old_files: bool = True
    max_raw_files_to_keep: int = 10
    max_processed_files_to_keep: int = 10

    # Data management settings
    archive_old_data: bool = True
    archive_after_days: int = 30
    
    class Config:
        env_file = "../.env"  # Look for .env in parent directory
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
