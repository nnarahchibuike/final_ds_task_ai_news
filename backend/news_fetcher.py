"""
News fetcher module for retrieving news articles from RSS feeds.
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
import ssl
import urllib.request
import urllib3
from loguru import logger
from config import get_settings
import hashlib

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

settings = get_settings()

# Configure SSL context to handle certificate issues
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Set up feedparser to use custom SSL context and user agent
feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


class NewsFetcher:
    """Handles fetching news articles from RSS feeds."""
    
    def __init__(self):
        """Initialize the news fetcher."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DS-Task-AI-News/1.0 (News Aggregator)'
        })
        logger.info("Initialized NewsFetcher")
    
    def fetch_from_rss(self, rss_url: str, category: str = "general") -> List[Dict[str, Any]]:
        """
        Fetch articles from a single RSS feed.

        Args:
            rss_url: URL of the RSS feed
            category: Category of the RSS feed

        Returns:
            List of article dictionaries
        """
        try:
            logger.info(f"Fetching from RSS feed: {rss_url} (category: {category})")

            # Use requests with SSL verification disabled for better compatibility
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            try:
                response = requests.get(rss_url, headers=headers, verify=False, timeout=30)
                response.raise_for_status()
                feed = feedparser.parse(response.content)
            except Exception as req_error:
                logger.warning(f"Requests failed for {rss_url}, trying feedparser directly: {req_error}")
                feed = feedparser.parse(rss_url)

            if feed.bozo:
                logger.warning(f"RSS feed may have issues: {rss_url} - {getattr(feed, 'bozo_exception', 'Unknown error')}")

            articles = []

            for entry in feed.entries[:settings.max_articles_per_feed]:
                article = self._parse_rss_entry(entry, rss_url, category)
                if article:
                    articles.append(article)

            logger.info(f"Fetched {len(articles)} articles from {rss_url} (category: {category})")
            return articles

        except Exception as e:
            logger.error(f"Error fetching from RSS feed {rss_url}: {str(e)}")
            return []
    
    def _parse_rss_entry(self, entry: Any, source_url: str, category: str = "general") -> Optional[Dict[str, Any]]:
        """
        Parse a single RSS entry into an article dictionary.

        Args:
            entry: RSS entry object
            source_url: Source RSS feed URL
            category: Category of the RSS feed

        Returns:
            Article dictionary or None if parsing fails
        """
        try:
            # Extract basic information
            title = getattr(entry, 'title', '')
            link = getattr(entry, 'link', '')
            summary = getattr(entry, 'summary', '')
            
            # Parse publication date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'published'):
                try:
                    published = datetime.fromisoformat(entry.published.replace('Z', '+00:00'))
                except:
                    published = datetime.now()
            else:
                published = datetime.now()
            
            # Extract content
            content = self._extract_content(entry)
            
            # Clean HTML from summary and content
            summary = self._clean_html(summary)
            content = self._clean_html(content)
            
            source_name = self._extract_source_name(source_url)
            
            article = {
                'id': self.generate_article_id(title, link, source_name),
                'title': title,
                'link': link,
                'summary': summary,
                'content': content,
                'published': published.isoformat(),
                'source_url': source_url,
                'source_name': source_name,
                'category': category,
                'fetched_at': datetime.now().isoformat()
            }
            
            return article
            
        except Exception as e:
            logger.error(f"Error parsing RSS entry: {str(e)}")
            return None
    
    def _extract_content(self, entry: Any) -> str:
        """Extract content from RSS entry."""
        content = ""
        
        # Try different content fields
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value if isinstance(entry.content, list) else entry.content
        elif hasattr(entry, 'description'):
            content = entry.description
        elif hasattr(entry, 'summary'):
            content = entry.summary
        
        return content
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and clean text."""
        if not text:
            return ""
        
        soup = BeautifulSoup(text, 'html.parser')
        cleaned = soup.get_text(separator=' ', strip=True)
        
        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def _extract_source_name(self, source_url: str) -> str:
        """Extract source name from RSS URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(source_url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Extract main domain name
            parts = domain.split('.')
            if len(parts) >= 2:
                return parts[0].title()
            
            return domain.title()
            
        except:
            return "Unknown"
    
    def fetch_all_feeds(self) -> List[Dict[str, Any]]:
        """
        Fetch articles from all configured RSS feeds.

        Returns:
            List of all articles from all feeds
        """
        all_articles = []

        for category, rss_urls in settings.rss_feeds.items():
            logger.info(f"Fetching articles from {category} category ({len(rss_urls)} feeds)")

            for rss_url in rss_urls:
                articles = self.fetch_from_rss(rss_url, category)
                all_articles.extend(articles)

        logger.info(f"Fetched total of {len(all_articles)} articles from all feeds")
        return all_articles

    def fetch_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Fetch articles from RSS feeds of a specific category.

        Args:
            category: Category name to fetch articles from

        Returns:
            List of articles from the specified category
        """
        if category not in settings.rss_feeds:
            logger.warning(f"Category '{category}' not found in RSS feeds configuration")
            return []

        all_articles = []
        rss_urls = settings.rss_feeds[category]

        logger.info(f"Fetching articles from {category} category ({len(rss_urls)} feeds)")

        for rss_url in rss_urls:
            articles = self.fetch_from_rss(rss_url, category)
            all_articles.extend(articles)

        logger.info(f"Fetched {len(all_articles)} articles from {category} category")
        return all_articles

    def get_available_categories(self) -> List[str]:
        """
        Get list of available RSS feed categories.

        Returns:
            List of category names
        """
        return list(settings.rss_feeds.keys())
    
    def save_raw_articles(self, articles: List[Dict[str, Any]]) -> str:
        """
        Save raw articles to JSON file.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Path to saved file
        """
        os.makedirs(settings.raw_news_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raw_articles_{timestamp}.json"
        filepath = os.path.join(settings.raw_news_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(articles)} raw articles to {filepath}")
        return filepath

    @staticmethod
    def generate_article_id(title: str, link: str, source_name: str) -> str:
        """
        Generate a unique article ID using the same logic as the vector store (Pinecone):
        article_id = f"{source_name}_{md5(title+link)}"
        Args:
            title: The article's title
            link: The article's URL
            source_name: The article's source name
        Returns:
            A unique string ID
        """
        content_hash = hashlib.md5(f"{title}{link}".encode()).hexdigest()
        return f"{source_name or 'unknown'}_{content_hash}"


# Global news fetcher instance
news_fetcher = None


def get_news_fetcher() -> NewsFetcher:
    """Get or create the global news fetcher instance."""
    global news_fetcher
    if news_fetcher is None:
        news_fetcher = NewsFetcher()
    return news_fetcher
