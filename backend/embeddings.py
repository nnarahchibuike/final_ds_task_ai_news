"""
Embeddings module for generating vector representations of news articles using Cohere.
"""
import cohere
import time
from typing import List, Dict, Any
from loguru import logger
from config import get_settings

settings = get_settings()


class EmbeddingGenerator:
    """Handles embedding generation using Cohere API."""
    
    def __init__(self):
        """Initialize the embedding generator with Cohere client."""
        if not settings.cohere_api_key:
            raise ValueError("COHERE_API_KEY environment variable is required")
        
        self.client = cohere.Client(settings.cohere_api_key)
        self.model = settings.embedding_model
        logger.info(f"Initialized EmbeddingGenerator with model: {self.model}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts with rate limiting for trial accounts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        try:
            if not texts:
                return []

            # For trial accounts, process in smaller batches with rate limiting
            # Trial limit: 100,000 tokens per minute
            # Estimate ~100 tokens per 75 words, so ~1000 tokens per article
            max_batch_size = settings.cohere_batch_size
            delay_between_batches = settings.cohere_rate_limit_delay

            all_embeddings = []

            for i in range(0, len(texts), max_batch_size):
                batch = texts[i:i + max_batch_size]

                logger.info(f"Generating embeddings for batch {i//max_batch_size + 1}: {len(batch)} texts")

                # Add delay between batches to respect rate limits
                if i > 0:
                    logger.info(f"Rate limiting: waiting {delay_between_batches} seconds...")
                    time.sleep(delay_between_batches)

                response = self.client.embed(
                    texts=batch,
                    model=self.model,
                    input_type="search_document"
                )

                batch_embeddings = response.embeddings
                all_embeddings.extend(batch_embeddings)

                logger.info(f"Successfully generated {len(batch_embeddings)} embeddings for batch")

            logger.info(f"Successfully generated {len(all_embeddings)} total embeddings")
            return all_embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Search query string
            
        Returns:
            Embedding vector for the query
        """
        try:
            logger.info(f"Generating query embedding for: {query}")
            
            response = self.client.embed(
                texts=[query],
                model=self.model,
                input_type="search_query"
            )
            
            embedding = response.embeddings[0]
            logger.info("Successfully generated query embedding")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise
    
    def prepare_text_for_embedding(self, article: Dict[str, Any]) -> str:
        """
        Prepare article text for embedding by combining title, summary, and content.
        
        Args:
            article: Article dictionary with title, summary, and content
            
        Returns:
            Combined text string for embedding
        """
        title = article.get("title", "")
        summary = article.get("summary", "")
        content = article.get("content", "")
        
        # Combine title, summary, and content with appropriate weighting
        combined_text = f"Title: {title}\n\nSummary: {summary}\n\nContent: {content}"
        
        # Truncate if too long (Cohere has token limits)
        max_chars = 8000  # Conservative limit
        if len(combined_text) > max_chars:
            combined_text = combined_text[:max_chars] + "..."
        
        return combined_text


# Global embedding generator instance
embedding_generator = None


def get_embedding_generator() -> EmbeddingGenerator:
    """Get or create the global embedding generator instance."""
    global embedding_generator
    if embedding_generator is None:
        embedding_generator = EmbeddingGenerator()
    return embedding_generator
