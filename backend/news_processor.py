"""
News processing module for cleaning, enhancing, and preparing articles for vector storage.
"""
import json
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

import html2text
from bs4 import BeautifulSoup
from groq import Groq
from loguru import logger

try:
    from config import get_settings
except ImportError:
    try:
        from .config import get_settings
    except ImportError:
        from backend.config import get_settings

settings = get_settings()


class NewsProcessor:
    """Handles processing of raw news articles into clean, enhanced format."""
    
    def __init__(self):
        """Initialize the news processor with Groq client."""
        self.groq_client = None
        if settings.groq_api_key:
            try:
                self.groq_client = Groq(api_key=settings.groq_api_key)
                logger.info("Initialized NewsProcessor with Groq client")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")
        else:
            logger.warning("No Groq API key provided - AI enhancement disabled")
        
        # Initialize HTML to text converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0  # Don't wrap lines
        
    def process_raw_news_files(self) -> List[str]:
        """
        Process all raw news files and create processed versions.
        
        Returns:
            List of processed file paths
        """
        raw_dir = Path(settings.raw_news_dir)
        processed_dir = Path(settings.processed_news_dir)
        
        # Ensure processed directory exists
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        processed_files = []
        
        # Find all raw news files
        if not raw_dir.exists():
            logger.warning(f"Raw news directory does not exist: {raw_dir}")
            return processed_files
        
        raw_files = list(raw_dir.glob("*.json"))
        logger.info(f"Found {len(raw_files)} raw news files to process")
        
        for raw_file in raw_files:
            try:
                processed_file = self._process_single_file(raw_file, processed_dir)
                if processed_file:
                    processed_files.append(processed_file)
            except Exception as e:
                logger.error(f"Error processing file {raw_file}: {e}")
        
        logger.info(f"Successfully processed {len(processed_files)} files")
        return processed_files
    
    def _process_single_file(self, raw_file: Path, processed_dir: Path) -> Optional[str]:
        """
        Process a single raw news file.
        
        Args:
            raw_file: Path to raw news JSON file
            processed_dir: Directory to save processed file
            
        Returns:
            Path to processed file or None if failed
        """
        try:
            # Load raw articles
            with open(raw_file, 'r', encoding='utf-8') as f:
                raw_articles = json.load(f)
            
            if not raw_articles:
                logger.warning(f"No articles found in {raw_file}")
                return None
            
            logger.info(f"Processing {len(raw_articles)} articles from {raw_file}")
            
            # Process articles with batch AI enhancement
            processed_articles = self._process_articles_batch(raw_articles)
            
            # Generate processed filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            processed_filename = f"processed_news_{timestamp}.json"
            processed_filepath = processed_dir / processed_filename
            
            # Save processed articles
            with open(processed_filepath, 'w', encoding='utf-8') as f:
                json.dump(processed_articles, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(processed_articles)} processed articles to {processed_filepath}")
            return str(processed_filepath)
            
        except Exception as e:
            logger.error(f"Error processing file {raw_file}: {e}")
            return None

    def _process_articles_batch(self, raw_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process articles in batches with optimized Groq API usage.

        Args:
            raw_articles: List of raw article dictionaries

        Returns:
            List of processed articles with AI summaries
        """
        processed_articles = []

        # Step 1: Process articles without AI (ID generation, content cleaning)
        articles_for_ai = []
        for article in raw_articles:
            processed_article = self._process_single_article_without_ai(article)
            if processed_article:
                processed_articles.append(processed_article)
                articles_for_ai.append(processed_article)

        # Step 2: Generate AI summaries in batches
        if self.groq_client and articles_for_ai:
            logger.info(f"Generating AI summaries for {len(articles_for_ai)} articles using batch processing")
            self._generate_summaries_batch(articles_for_ai)

        return processed_articles

    def _process_single_article_without_ai(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single article without AI enhancement (for batch processing).

        Args:
            article: Raw article dictionary

        Returns:
            Processed article dictionary without AI summary
        """
        try:
            # Generate unique ID
            unique_id = self._generate_article_id(article)

            # Clean content
            cleaned_content = self._clean_content(article.get('content', ''))

            # Create base processed article
            processed_article = {
                'id': unique_id,
                'title': article.get('title', '').strip(),
                'content': cleaned_content,
                'url': article.get('url', ''),
                'date': article.get('date', ''),
                'author': article.get('author', ''),
                'slug': article.get('slug', ''),
                'categories': article.get('categories', []),
                'tags': article.get('tags', []),
                'source_feed': article.get('source_feed', '')
            }

            return processed_article

        except Exception as e:
            logger.error(f"Error processing article '{article.get('title', 'Unknown')}': {e}")
            return None

    def _process_single_article(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single article: clean content, generate ID, enhance with AI.
        
        Args:
            article: Raw article dictionary
            
        Returns:
            Processed article dictionary or None if failed
        """
        try:
            # Generate unique ID
            unique_id = self._generate_article_id(article)
            
            # Clean content
            cleaned_content = self._clean_content(article.get('content', ''))
            
            # Create base processed article (removed metadata fields as requested)
            processed_article = {
                'id': unique_id,
                'title': article.get('title', '').strip(),
                'content': cleaned_content,
                'url': article.get('url', ''),
                'date': article.get('date', ''),
                'author': article.get('author', ''),
                'slug': article.get('slug', ''),
                'categories': article.get('categories', []),
                'tags': article.get('tags', []),  # Keep original tags without processing
                'source_feed': article.get('source_feed', '')
            }
            
            # Generate AI summary only (no tag/category processing)
            if self.groq_client:
                summary = self._generate_summary(processed_article)
                if summary:
                    processed_article['ai_summary'] = summary
            
            return processed_article
            
        except Exception as e:
            logger.error(f"Error processing article '{article.get('title', 'Unknown')}': {e}")
            return None
    
    def _generate_article_id(self, article: Dict[str, Any]) -> str:
        """
        Generate a uniform ID for an article using MD5 hash.
        Format: {source_name}_{md5_hash}

        Args:
            article: Article dictionary

        Returns:
            Unique article ID in format: source_name_md5hash
        """
        # Create hash from title and URL for consistency
        content_for_hash = f"{article.get('title', '')}{article.get('url', '')}"
        md5_hash = hashlib.md5(content_for_hash.encode('utf-8')).hexdigest()

        # Extract source name from feed URL
        source_feed = article.get('source_feed', 'unknown')
        if source_feed == 'unknown':
            source_name = 'unknown'
        else:
            # Extract domain or filename from URL
            if '://' in source_feed:
                # Extract domain name
                domain = source_feed.split('://')[1].split('/')[0]
                source_name = domain.replace('www.', '').replace('.com', '').replace('.', '_')
            else:
                # Extract filename
                source_name = source_feed.split('/')[-1].replace('.xml', '').replace('.rss', '').replace('.', '_')

        # Clean source name to be URL-safe and ensure it's not empty
        source_name = re.sub(r'[^a-zA-Z0-9_]', '_', source_name)
        if not source_name or source_name == '_':
            source_name = 'unknown'

        return f"{source_name}_{md5_hash}"
    
    def _clean_content(self, content: str) -> str:
        """
        Clean HTML tags and formatting from article content.
        
        Args:
            content: Raw content string
            
        Returns:
            Cleaned content string
        """
        if not content or not settings.content_cleaning_enabled:
            return content
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Convert to text using html2text
            text = self.html_converter.handle(str(soup))
            
            # Clean up extra whitespace
            text = re.sub(r'\n\s*\n', '\n\n', text)  # Remove excessive newlines
            text = re.sub(r'[ \t]+', ' ', text)      # Normalize spaces
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.warning(f"Error cleaning content: {e}")
            return content

    def _generate_summaries_batch(self, articles: List[Dict[str, Any]]) -> None:
        """
        Generate AI summaries for multiple articles in batches to optimize Groq API usage.

        Args:
            articles: List of processed articles to generate summaries for
        """
        if not self.groq_client:
            return

        # Use fixed batch size of 20 articles
        batch_size = 20

        # Process articles in batches
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]

            try:
                # Rate limiting - respect 30 calls per minute
                time.sleep(settings.groq_rate_limit_delay)

                logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} articles")

                # Generate summaries for the batch
                summaries = self._generate_batch_summaries(batch)

                # Assign summaries back to articles
                for j, summary in enumerate(summaries):
                    if j < len(batch) and summary:
                        batch[j]['ai_summary'] = summary

            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                # Fallback to individual processing for this batch
                self._fallback_individual_summaries(batch)



    def _generate_batch_summaries(self, articles: List[Dict[str, Any]]) -> List[str]:
        """
        Generate summaries for a batch of articles in a single API call.

        Args:
            articles: List of articles to summarize

        Returns:
            List of generated summaries
        """
        target_words = (settings.summary_min_words + settings.summary_max_words) // 2

        # Prepare batch prompt
        batch_prompt = self._create_batch_prompt(articles, target_words)

        try:
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional news summarizer. Create exactly {target_words} words for each summary. Respond with summaries separated by '---SUMMARY_SEPARATOR---' in the exact order requested."
                    },
                    {"role": "user", "content": batch_prompt}
                ],
                max_tokens=int(target_words * len(articles) * 1.5),  # Buffer for all summaries
                temperature=0.3
            )

            # Parse the response to extract individual summaries
            response_text = response.choices[0].message.content.strip()
            summaries = self._parse_batch_response(response_text, len(articles))

            # Log batch results
            total_words = sum(len(summary.split()) for summary in summaries if summary)
            avg_words = total_words / len(summaries) if summaries else 0
            logger.info(f"Batch summary generation completed: {len(summaries)} summaries, avg {avg_words:.1f} words")

            return summaries

        except Exception as e:
            logger.error(f"Error in batch summary generation: {e}")
            return [''] * len(articles)  # Return empty summaries on error

    def _generate_summary(self, article: Dict[str, Any]) -> str:
        """
        Generate AI summary for an article with consistent length.

        Args:
            article: Article dictionary

        Returns:
            AI-generated summary with consistent length
        """
        try:
            # Rate limiting
            time.sleep(settings.groq_rate_limit_delay)

            content = article.get('content', '')
            title = article.get('title', '')

            # Truncate content if too long (Groq has token limits)
            max_content_length = 3000
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."

            # More specific prompt for consistent length
            target_words = (settings.summary_min_words + settings.summary_max_words) // 2

            prompt = f"""
            Create a news summary that is EXACTLY {target_words} words long. Count your words carefully.

            Title: {title}

            Content: {content}

            Requirements:
            - EXACTLY {target_words} words (no more, no less)
            - Capture the main points and key information
            - Be objective and factual
            - Use clear, readable language
            - Do not include any introductory phrases like "This article discusses" or "The summary is"
            - Start directly with the content

            Write your {target_words}-word summary:
            """

            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": f"You are a professional news summarizer. You MUST create summaries that are exactly {target_words} words long. Count your words carefully and ensure the exact word count."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=int(target_words * 1.5),  # Allow some buffer for token conversion
                temperature=0.3  # Lower temperature for more consistent output
            )

            summary = response.choices[0].message.content.strip()

            # Log word count for monitoring
            word_count = len(summary.split())
            logger.debug(f"Generated summary for '{title[:50]}...' - Word count: {word_count}")

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return ""

    def _create_batch_prompt(self, articles: List[Dict[str, Any]], target_words: int) -> str:
        """
        Create a batch prompt for multiple articles.

        Args:
            articles: List of articles to summarize
            target_words: Target word count for each summary

        Returns:
            Formatted batch prompt
        """
        prompt = f"""Create news summaries for the following {len(articles)} articles. Each summary must be EXACTLY {target_words} words.

IMPORTANT INSTRUCTIONS:
- Create exactly {target_words} words for each summary
- Separate each summary with '---SUMMARY_SEPARATOR---'
- Maintain the same order as the articles below
- Be objective and factual
- Start directly with content (no introductory phrases)

"""

        for i, article in enumerate(articles, 1):
            title = article.get('title', '')
            content = article.get('content', '')

            # Truncate content to fit within token limits
            max_content_length = settings.groq_max_content_length_per_article
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."

            prompt += f"""
ARTICLE {i}:
Title: {title}
Content: {content}

"""

        prompt += f"""
Now provide exactly {target_words} words for each of the {len(articles)} articles above, separated by '---SUMMARY_SEPARATOR---':"""

        return prompt

    def _parse_batch_response(self, response_text: str, expected_count: int) -> List[str]:
        """
        Parse batch response to extract individual summaries.

        Args:
            response_text: Raw response from Groq API
            expected_count: Expected number of summaries

        Returns:
            List of individual summaries
        """
        try:
            # Split by separator
            summaries = response_text.split('---SUMMARY_SEPARATOR---')

            # Clean up summaries
            cleaned_summaries = []
            for summary in summaries:
                cleaned = summary.strip()
                if cleaned:
                    cleaned_summaries.append(cleaned)

            # Ensure we have the expected number of summaries
            while len(cleaned_summaries) < expected_count:
                cleaned_summaries.append('')  # Add empty summary for missing ones

            # Truncate if we have too many
            cleaned_summaries = cleaned_summaries[:expected_count]

            return cleaned_summaries

        except Exception as e:
            logger.error(f"Error parsing batch response: {e}")
            return [''] * expected_count

    def _fallback_individual_summaries(self, articles: List[Dict[str, Any]]) -> None:
        """
        Fallback to individual summary generation when batch processing fails.

        Args:
            articles: List of articles to process individually
        """
        logger.warning(f"Falling back to individual processing for {len(articles)} articles")

        for article in articles:
            try:
                summary = self._generate_summary(article)
                if summary:
                    article['ai_summary'] = summary
            except Exception as e:
                logger.error(f"Error in fallback summary generation for '{article.get('title', 'Unknown')}': {e}")


def get_news_processor() -> NewsProcessor:
    """Get a NewsProcessor instance."""
    return NewsProcessor()
