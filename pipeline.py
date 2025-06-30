#!/usr/bin/env python3
"""
Standalone News Processing Pipeline

This script handles the complete news processing workflow:
1. Fetch raw news from RSS feeds
2. Process and clean articles with AI enhancement
3. Generate embeddings and store in vector database
4. Save processed news for API consumption

Run this script before starting the FastAPI application.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

# Add backend directory to path for imports
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from config import get_settings
    from news_fetcher import get_news_fetcher
    from news_processor import get_news_processor
    from vector_store import get_vector_store
    from embeddings import get_embedding_generator
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running this script from the project root directory")
    sys.exit(1)

# Initialize settings
settings = get_settings()


class NewsPipeline:
    """Standalone news processing pipeline."""
    
    def __init__(self):
        """Initialize the pipeline with required components."""
        self.settings = settings
        self.start_time = datetime.now()
        self.stats = {
            'raw_articles_fetched': 0,
            'articles_processed': 0,
            'articles_stored': 0,
            'errors': 0,
            'processing_time': 0
        }
        
        # Ensure data directories exist
        os.makedirs(self.settings.raw_news_dir, exist_ok=True)
        os.makedirs(self.settings.processed_news_dir, exist_ok=True)
        
        logger.info("Initialized News Processing Pipeline")
    
    def run(self) -> bool:
        """
        Execute the complete pipeline.
        
        Returns:
            True if pipeline completed successfully, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("🚀 Starting News Processing Pipeline")
            logger.info("=" * 60)
            
            # Step 1: Fetch raw news from RSS feeds
            if not self._step_1_fetch_raw_news():
                logger.error("❌ Step 1 failed: Raw news fetching")
                return False
            
            # Step 2: Process and clean articles
            if not self._step_2_process_articles():
                logger.error("❌ Step 2 failed: Article processing")
                return False
            
            # Step 3: Generate embeddings and store in vector database
            if not self._step_3_vector_operations():
                logger.error("❌ Step 3 failed: Vector operations")
                return False
            
            # Step 4: Create consolidated output for API
            if not self._step_4_create_api_output():
                logger.error("❌ Step 4 failed: API output creation")
                return False
            
            # Generate final summary
            self._generate_summary()
            
            logger.info("✅ Pipeline completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"💥 Pipeline failed with error: {str(e)}")
            self.stats['errors'] += 1
            return False
        finally:
            self.stats['processing_time'] = (datetime.now() - self.start_time).total_seconds()
    
    def _step_1_fetch_raw_news(self) -> bool:
        """Step 1: Fetch raw news from RSS feeds."""
        try:
            logger.info("📡 Step 1: Fetching raw news from RSS feeds...")
            
            news_fetcher = get_news_fetcher()
            articles = news_fetcher.fetch_all_feeds()
            
            if not articles:
                logger.warning("⚠️  No articles fetched from RSS feeds")
                return True  # Not an error, just no new content
            
            # Save raw articles
            raw_file_path = news_fetcher.save_raw_articles(articles)
            self.stats['raw_articles_fetched'] = len(articles)
            
            logger.info(f"✅ Step 1 completed: Fetched {len(articles)} articles")
            logger.info(f"📁 Raw articles saved to: {raw_file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in Step 1: {str(e)}")
            self.stats['errors'] += 1
            return False
    
    def _step_2_process_articles(self) -> bool:
        """Step 2: Process and clean articles with AI enhancement."""
        try:
            logger.info("🔄 Step 2: Processing and cleaning articles...")
            
            news_processor = get_news_processor()
            processed_files = news_processor.process_raw_news_files()
            
            if not processed_files:
                logger.warning("⚠️  No processed files generated")
                return True  # Not an error if no raw files to process
            
            # Count total processed articles
            total_processed = 0
            for processed_file in processed_files:
                try:
                    with open(processed_file, 'r', encoding='utf-8') as f:
                        articles = json.load(f)
                        total_processed += len(articles)
                except Exception as e:
                    logger.error(f"Error counting articles in {processed_file}: {e}")
            
            self.stats['articles_processed'] = total_processed
            
            logger.info(f"✅ Step 2 completed: Processed {total_processed} articles")
            logger.info(f"📁 Processed files: {len(processed_files)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in Step 2: {str(e)}")
            self.stats['errors'] += 1
            return False
    
    def _step_3_vector_operations(self) -> bool:
        """Step 3: Generate embeddings and store in vector database."""
        try:
            logger.info("🧠 Step 3: Generating embeddings and storing in vector database...")
            
            # Load all processed articles
            processed_dir = Path(self.settings.processed_news_dir)
            all_processed_articles = []
            
            for processed_file in processed_dir.glob("processed_news_*.json"):
                try:
                    with open(processed_file, 'r', encoding='utf-8') as f:
                        articles = json.load(f)
                        all_processed_articles.extend(articles)
                except Exception as e:
                    logger.error(f"Error loading {processed_file}: {e}")
            
            if not all_processed_articles:
                logger.warning("⚠️  No processed articles found for vector storage")
                return True
            
            # Convert to vector store format
            vector_articles = self._convert_to_vector_format(all_processed_articles)
            
            # Store in vector database
            if vector_articles:
                vector_store = get_vector_store()
                added_count = vector_store.add_articles(vector_articles)
                self.stats['articles_stored'] = added_count
                
                logger.info(f"✅ Step 3 completed: Stored {added_count} articles in vector database")
            else:
                logger.warning("⚠️  No articles converted for vector storage")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in Step 3: {str(e)}")
            self.stats['errors'] += 1
            return False
    
    def _step_4_create_api_output(self) -> bool:
        """Step 4: Create consolidated output for API consumption."""
        try:
            logger.info("📦 Step 4: Creating consolidated output for API...")
            
            # Load all processed articles
            processed_dir = Path(self.settings.processed_news_dir)
            all_articles = []
            
            for processed_file in processed_dir.glob("processed_news_*.json"):
                try:
                    with open(processed_file, 'r', encoding='utf-8') as f:
                        articles = json.load(f)
                        all_articles.extend(articles)
                except Exception as e:
                    logger.error(f"Error loading {processed_file}: {e}")
            
            if not all_articles:
                logger.warning("⚠️  No articles found for API output")
                return True
            
            # Create consolidated file for API
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            api_output_file = processed_dir / f"api_articles_{timestamp}.json"
            
            # Format articles for API consumption
            api_articles = []
            for article in all_articles:
                api_article = {
                    'id': article.get('id', ''),
                    'title': article.get('title', ''),
                    'content': article.get('content', ''),
                    'date': article.get('date', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source_feed', ''),
                    'categories': article.get('categories', []),  # Use original categories
                    'tags': article.get('tags', []),  # Use original tags
                    'summary': article.get('ai_summary', ''),
                    'author': article.get('author', ''),
                    'slug': article.get('slug', '')
                }
                api_articles.append(api_article)
            
            # Save consolidated file
            with open(api_output_file, 'w', encoding='utf-8') as f:
                json.dump(api_articles, f, indent=2, ensure_ascii=False)
            
            # Create latest symlink for API to use
            latest_file = processed_dir / "latest_articles.json"
            if latest_file.exists():
                latest_file.unlink()
            latest_file.symlink_to(api_output_file.name)
            
            logger.info(f"✅ Step 4 completed: Created API output with {len(api_articles)} articles")
            logger.info(f"📁 API file: {api_output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in Step 4: {str(e)}")
            self.stats['errors'] += 1
            return False
    
    def _convert_to_vector_format(self, processed_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert processed articles to vector store format."""
        vector_articles = []

        for article in processed_articles:
            vector_article = {
                'title': article.get('title', ''),
                'link': article.get('url', ''),
                'summary': article.get('ai_summary', article.get('content', '')[:500]),
                'published': article.get('date', ''),
                'source_name': article.get('source_feed', '').split('/')[-1].replace('.xml', '').replace('.rss', ''),
                'category': article.get('categories', ['general'])[0] if article.get('categories') else 'general',
                'content': article.get('content', ''),
                'tags': article.get('tags', []),  # Use original tags without enhancement
                'processed_id': article.get('id', '')
            }
            vector_articles.append(vector_article)

        return vector_articles
    
    def _generate_summary(self):
        """Generate and display pipeline execution summary."""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        logger.info("=" * 60)
        logger.info("📊 PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"⏱️  Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏱️  End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏱️  Duration: {duration}")
        logger.info(f"📡 Raw Articles Fetched: {self.stats['raw_articles_fetched']}")
        logger.info(f"🔄 Articles Processed: {self.stats['articles_processed']}")
        logger.info(f"🧠 Articles Stored in Vector DB: {self.stats['articles_stored']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        
        if self.stats['errors'] == 0:
            logger.info("🎉 Pipeline completed successfully with no errors!")
        else:
            logger.warning(f"⚠️  Pipeline completed with {self.stats['errors']} errors")
        
        logger.info("=" * 60)


def main():
    """Main pipeline execution function."""
    try:
        # Configure logging
        logger.remove()  # Remove default handler
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO"
        )
        
        # Add file logging
        log_file = Path("pipeline.log")
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="10 MB"
        )
        
        logger.info("Starting News Processing Pipeline...")
        
        # Create and run pipeline
        pipeline = NewsPipeline()
        success = pipeline.run()
        
        if success:
            logger.info("🎉 Pipeline execution completed successfully!")
            logger.info("💡 You can now start the FastAPI application:")
            logger.info("   python backend/main.py")
            sys.exit(0)
        else:
            logger.error("💥 Pipeline execution failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
