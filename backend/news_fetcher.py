"""
News fetcher module for retrieving news articles from RSS feeds.
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Set
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
        self._seen_articles: Set[str] = set()  # For deduplication
        self._load_seen_articles()
        logger.info("Initialized NewsFetcher")

    def _load_seen_articles(self):
        """Load previously seen article IDs for deduplication."""
        if not settings.deduplication_enabled:
            return

        try:
            seen_file = os.path.join(settings.raw_news_dir, 'seen_articles.json')
            if os.path.exists(seen_file):
                with open(seen_file, 'r', encoding='utf-8') as f:
                    seen_list = json.load(f)
                    self._seen_articles = set(seen_list)
                logger.info(f"Loaded {len(self._seen_articles)} seen article IDs")
        except Exception as e:
            logger.warning(f"Could not load seen articles: {e}")

    def _save_seen_articles(self):
        """Save seen article IDs for future deduplication."""
        if not settings.deduplication_enabled:
            return

        try:
            os.makedirs(settings.raw_news_dir, exist_ok=True)
            seen_file = os.path.join(settings.raw_news_dir, 'seen_articles.json')
            with open(seen_file, 'w', encoding='utf-8') as f:
                json.dump(list(self._seen_articles), f)
            logger.debug(f"Saved {len(self._seen_articles)} seen article IDs")
        except Exception as e:
            logger.warning(f"Could not save seen articles: {e}")

    def _generate_article_hash(self, article: Dict[str, Any]) -> str:
        """Generate a hash for an article for deduplication."""
        content_for_hash = f"{article.get('title', '')}{article.get('url', '')}"
        return hashlib.md5(content_for_hash.encode('utf-8')).hexdigest()

    def _is_duplicate(self, article: Dict[str, Any]) -> bool:
        """Check if an article is a duplicate."""
        if not settings.deduplication_enabled:
            return False

        article_hash = self._generate_article_hash(article)
        return article_hash in self._seen_articles

    def _mark_as_seen(self, article: Dict[str, Any]):
        """Mark an article as seen."""
        if settings.deduplication_enabled:
            article_hash = self._generate_article_hash(article)
            self._seen_articles.add(article_hash)

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

            # Parse RSS feed
            feed = feedparser.parse(rss_url)

            if feed.bozo:
                logger.warning(f"RSS feed may have issues: {rss_url} - {getattr(feed, 'bozo_exception', 'Unknown error')}")

            # Process entries
            articles = []
            for entry in feed.entries[:settings.max_articles_per_feed]:
                article = self._parse_rss_entry(entry, rss_url, category)
                if article and not self._is_duplicate(article):
                    articles.append(article)
                    self._mark_as_seen(article)
                else:
                    if article:
                        logger.debug(f"Skipping duplicate article: {article.get('title', 'Unknown')[:50]}...")

            logger.info(f"Fetched {len(articles)} new articles from {rss_url} (category: {category})")
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

            # Extract content using enhanced method
            content = self._extract_content(entry)

            # Extract categories from RSS tags
            categories = self._extract_categories(entry)

            # Extract tags from RSS entry
            tags = self._extract_tags(entry, categories)

            # Extract author information
            author = self._extract_author(entry)

            # Clean HTML from summary and content
            summary = self._clean_html(summary)
            content = self._clean_html(content)

            # Generate slug from title
            slug = self._generate_slug(title)

            source_name = self._extract_source_name(source_url)

            article = {
                'id': self.generate_article_id(title, link, source_name),
                'title': title,
                'url': link,
                'link': link,  # Keep both for compatibility
                'summary': summary,
                'content': content,
                'date': published.isoformat(),
                'published': published.isoformat(),  # Keep both for compatibility
                'author': author,
                'slug': slug,
                'categories': categories,
                'tags': tags,
                'source_feed': source_url,
                'source_url': source_url,  # Keep both for compatibility
                'source_name': source_name,
                'category': category,
                'fetched_at': datetime.now().isoformat()
            }

            return article

        except Exception as e:
            logger.error(f"Error parsing RSS entry: {str(e)}")
            return None
    
    def _extract_content(self, entry: Any) -> str:
        """Extract content from RSS entry using enhanced method from rss.py."""
        content = ""

        # Try different content fields in order of preference
        if hasattr(entry, 'content') and entry.content:
            if isinstance(entry.content, list) and len(entry.content) > 0:
                content = entry.content[0].value
            else:
                content = str(entry.content)
        elif hasattr(entry, 'description') and entry.description:
            content = entry.description
        elif hasattr(entry, 'summary') and entry.summary:
            content = entry.summary
        elif hasattr(entry, 'summary_detail') and entry.summary_detail:
            content = entry.summary_detail.value

        return content

    def _extract_categories(self, entry: Any) -> List[str]:
        """Extract categories from RSS entry."""
        categories = []

        if hasattr(entry, 'tags') and entry.tags:
            categories = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
        elif hasattr(entry, 'category') and entry.category:
            if isinstance(entry.category, list):
                categories = entry.category
            else:
                categories = [entry.category]

        return categories

    def _extract_tags(self, entry: Any, categories: List[str]) -> List[str]:
        """Extract tags from RSS entry."""
        tags = []

        if hasattr(entry, 'tags') and entry.tags:
            for tag in entry.tags:
                if hasattr(tag, 'term') and tag.term:
                    tags.append(tag.term)
                elif hasattr(tag, 'label') and tag.label:
                    tags.append(tag.label)

        # Use categories as tags if no tags found
        if not tags and categories:
            tags = categories.copy()

        return tags

    def _extract_author(self, entry: Any) -> str:
        """Extract author information from RSS entry."""
        author = ""

        if hasattr(entry, 'author') and entry.author:
            author = entry.author
        elif hasattr(entry, 'author_detail') and entry.author_detail:
            author = entry.author_detail.get('name', '')

        return author

    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title."""
        if not title:
            return ""

        slug = title.lower().replace(" ", "-").replace("'", "").replace('"', '')
        # Remove other special characters
        import re
        slug = re.sub(r'[^a-z0-9\-]', '', slug)
        # Remove multiple consecutive dashes
        slug = re.sub(r'-+', '-', slug)
        # Remove leading/trailing dashes
        slug = slug.strip('-')

        return slug
    
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

        # Save seen articles for deduplication
        self._save_seen_articles()

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
        
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
        filename = f"raw_news_{timestamp}.json"
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
