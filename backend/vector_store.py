"""
Vector store module for managing news articles in Pinecone.
"""
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
import json
import hashlib
from datetime import datetime
from loguru import logger
from config import get_settings
from embeddings import get_embedding_generator

settings = get_settings()


class VectorStore:
    """Handles vector database operations using Pinecone."""

    def __init__(self):
        """Initialize the vector store with Pinecone."""
        if not settings.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")

        # Initialize Pinecone client
        self.pc = Pinecone(api_key=settings.pinecone_api_key)

        self.index_name = settings.pinecone_index_name
        self.namespace = settings.pinecone_namespace

        # Check if index exists, create if not
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        if self.index_name not in existing_indexes:
            logger.info(f"Creating Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=settings.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )

        # Connect to index
        self.index = self.pc.Index(self.index_name)
        self.embedding_generator = get_embedding_generator()
        logger.info(f"Initialized VectorStore with Pinecone index: {self.index_name}")
    
    def add_articles(self, articles: List[Dict[str, Any]]) -> int:
        """
        Add articles to the vector store.

        Args:
            articles: List of article dictionaries

        Returns:
            Number of articles successfully added
        """
        if not articles:
            return 0

        try:
            logger.info(f"Adding {len(articles)} articles to vector store")

            # Prepare texts for embedding
            texts_for_embedding = []

            for i, article in enumerate(articles):
                # Use processed ID if available, otherwise generate one
                if article.get('processed_id'):
                    article_id = article['processed_id']
                else:
                    # Create unique ID using hash of title and link (fallback)
                    content_hash = hashlib.md5(
                        f"{article.get('title', '')}{article.get('link', '')}".encode()
                    ).hexdigest()
                    article_id = f"{article.get('source_name', 'unknown')}_{content_hash}"

                # Prepare text for embedding
                text = self.embedding_generator.prepare_text_for_embedding(article)
                texts_for_embedding.append((article_id, text, article))

            # Generate embeddings in batches
            batch_size = 100  # Pinecone batch limit
            added_count = 0

            for i in range(0, len(texts_for_embedding), batch_size):
                batch = texts_for_embedding[i:i + batch_size]
                batch_texts = [item[1] for item in batch]

                # Generate embeddings for this batch
                batch_embeddings = self.embedding_generator.generate_embeddings(batch_texts)

                # Prepare vectors for Pinecone
                vectors = []
                for j, (article_id, text, article) in enumerate(batch):
                    # Prepare metadata (Pinecone has metadata size limits)
                    # Use AI-enhanced data when available
                    summary = article.get('ai_summary', article.get('summary', ''))
                    tags = article.get('enhanced_tags', article.get('tags', []))
                    categories = article.get('enhanced_categories', article.get('categories', []))

                    metadata = {
                        'title': article.get('title', '')[:1000],  # Limit length
                        'link': article.get('link', ''),
                        'summary': summary[:2000],  # Limit length - prefer AI summary
                        'published': article.get('published', ''),
                        'source_name': article.get('source_name', ''),
                        'category': categories[0] if categories else article.get('category', 'general'),
                        'tags': tags[:10] if isinstance(tags, list) else [],  # Limit number of tags
                        'ai_enhanced': article.get('ai_enhanced', False),
                        'added_to_db': datetime.now().isoformat(),
                        'content_preview': text[:500]  # Store preview of content
                    }

                    vectors.append({
                        'id': article_id,
                        'values': batch_embeddings[j],
                        'metadata': metadata
                    })

                # Upsert to Pinecone
                self.index.upsert(
                    vectors=vectors,
                    namespace=self.namespace
                )

                added_count += len(vectors)
                logger.info(f"Added batch of {len(vectors)} articles to Pinecone")

            logger.info(f"Successfully added {added_count} articles to vector store")
            return added_count

        except Exception as e:
            logger.error(f"Error adding articles to vector store: {str(e)}")
            raise
    
    def search_similar_articles(self, query: str, n_results: int = None) -> List[Dict[str, Any]]:
        """
        Search for articles similar to the query.

        Args:
            query: Search query string
            n_results: Number of results to return (default from settings)

        Returns:
            List of similar articles with metadata
        """
        if n_results is None:
            n_results = settings.max_recommendations

        try:
            logger.info(f"Searching for articles similar to: {query}")

            # Generate query embedding
            query_embedding = self.embedding_generator.generate_query_embedding(query)

            # Search in Pinecone
            search_results = self.index.query(
                vector=query_embedding,
                top_k=n_results,
                include_metadata=True,
                namespace=self.namespace
            )

            # Format results
            articles = []
            for match in search_results.matches:
                similarity_score = match.score

                # Filter by similarity threshold
                if similarity_score >= settings.similarity_threshold:
                    metadata = match.metadata
                    article = {
                        'id': match.id,
                        'title': metadata.get('title', ''),
                        'link': metadata.get('link', ''),
                        'summary': metadata.get('summary', ''),
                        'published': metadata.get('published', ''),
                        'source_name': metadata.get('source_name', ''),
                        'category': metadata.get('category', 'general'),
                        'similarity_score': similarity_score,
                        'content_preview': metadata.get('content_preview', '')
                    }
                    articles.append(article)

            logger.info(f"Found {len(articles)} similar articles")
            return articles

        except Exception as e:
            logger.error(f"Error searching for similar articles: {str(e)}")
            raise

    def search_by_category(self, query: str, category: str, n_results: int = None) -> List[Dict[str, Any]]:
        """
        Search for articles similar to the query within a specific category.

        Args:
            query: Search query string
            category: Category to filter by
            n_results: Number of results to return (default from settings)

        Returns:
            List of similar articles from the specified category
        """
        if n_results is None:
            n_results = settings.max_recommendations

        try:
            logger.info(f"Searching for articles similar to: {query} in category: {category}")

            # Generate query embedding
            query_embedding = self.embedding_generator.generate_query_embedding(query)

            # Search in Pinecone with category filter
            search_results = self.index.query(
                vector=query_embedding,
                top_k=n_results * 2,  # Get more results to account for filtering
                include_metadata=True,
                namespace=self.namespace,
                filter={"category": {"$eq": category}}
            )

            # Format results
            articles = []
            for match in search_results.matches:
                similarity_score = match.score

                # Filter by similarity threshold
                if similarity_score >= settings.similarity_threshold:
                    metadata = match.metadata
                    article = {
                        'id': match.id,
                        'title': metadata.get('title', ''),
                        'link': metadata.get('link', ''),
                        'summary': metadata.get('summary', ''),
                        'published': metadata.get('published', ''),
                        'source_name': metadata.get('source_name', ''),
                        'category': metadata.get('category', 'general'),
                        'similarity_score': similarity_score,
                        'content_preview': metadata.get('content_preview', '')
                    }
                    articles.append(article)

                    # Stop if we have enough results
                    if len(articles) >= n_results:
                        break

            logger.info(f"Found {len(articles)} similar articles in category: {category}")
            return articles

        except Exception as e:
            logger.error(f"Error searching for similar articles in category {category}: {str(e)}")
            raise
    
    def get_article_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific article by its ID.

        Args:
            article_id: Unique article identifier

        Returns:
            Article dictionary or None if not found
        """
        try:
            # Fetch from Pinecone
            fetch_result = self.index.fetch(
                ids=[article_id],
                namespace=self.namespace
            )

            if article_id in fetch_result.vectors:
                vector_data = fetch_result.vectors[article_id]
                metadata = vector_data.metadata

                return {
                    'id': article_id,
                    'title': metadata.get('title', ''),
                    'link': metadata.get('link', ''),
                    'summary': metadata.get('summary', ''),
                    'content': metadata.get('content_preview', ''),
                    'published': metadata.get('published', ''),
                    'source_name': metadata.get('source_name', ''),
                }

            return None

        except Exception as e:
            logger.error(f"Error getting article by ID {article_id}: {str(e)}")
            return None

    def search_similar_by_id(self, article_id: str, n_results: int = None, exclude_source: bool = True) -> List[Dict[str, Any]]:
        """
        Search for articles similar to a specific article using its existing vector.
        This is much more efficient than creating a text query and re-embedding.

        Args:
            article_id: ID of the source article to find similar articles for
            n_results: Number of results to return (default from settings)
            exclude_source: Whether to exclude the source article from results

        Returns:
            List of similar articles with metadata, excluding the source article if requested
        """
        if n_results is None:
            n_results = settings.max_recommendations

        try:
            logger.info(f"Searching for articles similar to article ID: {article_id}")

            # First, fetch the source article to get its vector
            fetch_result = self.index.fetch(
                ids=[article_id],
                namespace=self.namespace
            )

            if article_id not in fetch_result.vectors:
                logger.warning(f"Article with ID {article_id} not found")
                return []

            # Get the source article's vector
            source_vector = fetch_result.vectors[article_id].values

            # Search using the existing vector directly (no re-embedding needed!)
            search_results = self.index.query(
                vector=source_vector,
                top_k=n_results + (1 if exclude_source else 0),  # +1 to account for source article
                include_metadata=True,
                namespace=self.namespace
            )

            # Format results
            articles = []
            for match in search_results.matches:
                # Skip the source article if requested
                if exclude_source and match.id == article_id:
                    continue

                similarity_score = match.score

                # Filter by similarity threshold
                if similarity_score >= settings.similarity_threshold:
                    metadata = match.metadata
                    article = {
                        'id': match.id,
                        'title': metadata.get('title', ''),
                        'link': metadata.get('link', ''),
                        'summary': metadata.get('summary', ''),
                        'published': metadata.get('published', ''),
                        'source_name': metadata.get('source_name', ''),
                        'category': metadata.get('category', 'general'),
                        'similarity_score': similarity_score,
                        'content_preview': metadata.get('content_preview', '')
                    }
                    articles.append(article)

                    # Stop if we have enough results
                    if len(articles) >= n_results:
                        break

            logger.info(f"Found {len(articles)} similar articles for article {article_id}")
            return articles

        except Exception as e:
            logger.error(f"Error searching for similar articles by ID {article_id}: {str(e)}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.

        Returns:
            Dictionary with collection statistics
        """
        try:
            # Get index stats from Pinecone
            index_stats = self.index.describe_index_stats()

            # Get total vector count
            total_vectors = 0
            if hasattr(index_stats, 'total_vector_count'):
                total_vectors = index_stats.total_vector_count
            elif hasattr(index_stats, 'namespaces') and self.namespace in index_stats.namespaces:
                total_vectors = index_stats.namespaces[self.namespace].vector_count

            return {
                'total_articles': total_vectors,
                'index_name': self.index_name,
                'namespace': self.namespace,
                'environment': 'serverless'  # New Pinecone uses serverless by default
            }

        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {'error': str(e)}

    def clear_collection(self) -> bool:
        """
        Clear all articles from the collection.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete all vectors in the namespace
            self.index.delete(delete_all=True, namespace=self.namespace)

            logger.info("Cleared all articles from vector store")
            return True

        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            return False


# Global vector store instance
vector_store = None


def get_vector_store() -> VectorStore:
    """Get or create the global vector store instance."""
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store
