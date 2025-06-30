"""
Recommender module for finding and ranking related news articles.
"""
import cohere
from typing import List, Dict, Any, Optional
from loguru import logger
from config import get_settings
from vector_store import get_vector_store

settings = get_settings()


class NewsRecommender:
    """Handles news recommendation using vector similarity and optional re-ranking."""

    def __init__(self):
        """Initialize the recommender with Cohere client."""
        # Initialize Cohere for re-ranking
        if settings.cohere_api_key:
            self.cohere_client = cohere.Client(settings.cohere_api_key)
        else:
            self.cohere_client = None
            logger.warning("Cohere API key not provided, re-ranking will be disabled")

        self.vector_store = get_vector_store()
        logger.info("Initialized NewsRecommender")
    
    def get_recommendations(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Get news recommendations based on a text query.

        Note: For article-to-article similarity, use get_similar_articles() instead,
        which is optimized to use existing vectors without re-embedding.

        Args:
            query: User query or interest description
            max_results: Maximum number of recommendations to return

        Returns:
            List of recommended articles with scores
        """
        if max_results is None:
            max_results = settings.max_recommendations
        
        try:
            logger.info(f"Getting recommendations for query: {query}")
            
            # Get initial similar articles from vector store
            similar_articles = self.vector_store.search_similar_articles(
                query=query,
                n_results=max_results * 2  # Get more for re-ranking
            )
            
            if not similar_articles:
                logger.info("No similar articles found")
                return []
            
            # Re-rank articles using Cohere if available
            if self.cohere_client and len(similar_articles) > 1:
                reranked_articles = self._rerank_articles(query, similar_articles)
            else:
                reranked_articles = similar_articles
            
            # Limit to requested number of results
            final_recommendations = reranked_articles[:max_results]

            logger.info(f"Returning {len(final_recommendations)} recommendations")
            return final_recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            raise
    
    def _rerank_articles(self, query: str, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Re-rank articles using Cohere's rerank API.
        
        Args:
            query: Original query
            articles: List of articles to re-rank
            
        Returns:
            Re-ranked list of articles
        """
        try:
            logger.info(f"Re-ranking {len(articles)} articles")
            
            # Prepare documents for re-ranking
            documents = []
            for article in articles:
                doc_text = f"{article['title']} {article['summary']}"
                documents.append(doc_text)
            
            # Use Cohere rerank
            rerank_response = self.cohere_client.rerank(
                model="rerank-english-v3.0",
                query=query,
                documents=documents
            )
            
            # Reorder articles based on rerank scores
            reranked_articles = []
            for result in rerank_response.results:
                original_article = articles[result.index]
                original_article['rerank_score'] = result.relevance_score
                reranked_articles.append(original_article)
            
            logger.info("Successfully re-ranked articles")
            return reranked_articles
            
        except Exception as e:
            logger.error(f"Error re-ranking articles: {str(e)}")
            # Return original order if re-ranking fails
            return articles
    

    
    def get_similar_articles(self, article_id: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Get articles similar to a specific article by ID.

        This method is now optimized to use the article's existing vector directly,
        eliminating redundant embedding generation and improving performance.

        Args:
            article_id: ID of the source article to find similar articles for
            max_results: Maximum number of similar articles to return

        Returns:
            List of similar articles excluding the source article
        """
        if max_results is None:
            max_results = settings.max_recommendations

        try:
            logger.info(f"Getting similar articles for article ID: {article_id}")

            # Use the optimized vector search method - no re-embedding needed!
            similar_articles = self.vector_store.search_similar_by_id(
                article_id=article_id,
                n_results=max_results * 2,  # Get more for potential re-ranking
                exclude_source=True  # Automatically excludes the source article
            )

            if not similar_articles:
                logger.info(f"No similar articles found for article {article_id}")
                return []

            # Optional: Re-rank articles using Cohere if available and beneficial
            # Note: For article-to-article similarity, vector similarity is often sufficient
            # Re-ranking is more useful for text queries than article-to-article matching
            if self.cohere_client and len(similar_articles) > max_results:
                # Only re-rank if we have more results than needed
                source_article = self.vector_store.get_article_by_id(article_id)
                if source_article:
                    query_text = f"{source_article['title']} {source_article.get('summary', '')}"
                    reranked_articles = self._rerank_articles(query_text, similar_articles)
                else:
                    reranked_articles = similar_articles
            else:
                reranked_articles = similar_articles

            # Limit to requested number of results
            final_results = reranked_articles[:max_results]

            logger.info(f"Returning {len(final_results)} similar articles for article {article_id}")
            return final_results

        except Exception as e:
            logger.error(f"Error getting similar articles for {article_id}: {str(e)}")
            raise

    def get_trending_topics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending topics based on recent articles.

        Note: This method now returns a simplified analysis based on article categories
        and titles without AI-generated insights.

        Args:
            limit: Number of trending topics to return

        Returns:
            List of trending topics with basic analysis
        """
        try:
            logger.info("Analyzing trending topics")

            # Get recent articles
            recent_articles = self.vector_store.search_similar_articles(
                query="news today current events",
                n_results=50
            )

            if not recent_articles:
                return []

            # Simple trending analysis based on categories and keywords
            category_counts = {}
            keyword_counts = {}

            for article in recent_articles:
                # Count categories
                category = article.get('category', 'general')
                category_counts[category] = category_counts.get(category, 0) + 1

                # Extract keywords from titles (simple approach)
                title_words = article.get('title', '').lower().split()
                for word in title_words:
                    if len(word) > 4:  # Only consider longer words
                        keyword_counts[word] = keyword_counts.get(word, 0) + 1

            # Create trending topics from top categories and keywords
            trending_topics = []

            # Add top categories
            sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
            for category, count in sorted_categories[:limit//2]:
                trending_topics.append({
                    "topic": category.title(),
                    "description": f"Popular category with {count} recent articles",
                    "reason": f"High activity in {category} news",
                    "article_count": count
                })

            # Add top keywords
            sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
            for keyword, count in sorted_keywords[:limit//2]:
                if len(trending_topics) < limit:
                    trending_topics.append({
                        "topic": keyword.title(),
                        "description": f"Frequently mentioned keyword in {count} articles",
                        "reason": f"High frequency in recent headlines",
                        "mention_count": count
                    })

            logger.info(f"Identified {len(trending_topics)} trending topics")
            return trending_topics[:limit]

        except Exception as e:
            logger.error(f"Error analyzing trending topics: {str(e)}")
            return []


# Global recommender instance
news_recommender = None


def get_news_recommender() -> NewsRecommender:
    """Get or create the global news recommender instance."""
    global news_recommender
    if news_recommender is None:
        news_recommender = NewsRecommender()
    return news_recommender
