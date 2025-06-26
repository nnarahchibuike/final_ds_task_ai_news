"""
Recommender module for finding and ranking related news articles.
"""
import cohere
from groq import Groq
from typing import List, Dict, Any, Optional
from loguru import logger
from config import get_settings
from vector_store import get_vector_store

settings = get_settings()


class NewsRecommender:
    """Handles news recommendation using vector similarity and AI re-ranking."""
    
    def __init__(self):
        """Initialize the recommender with Cohere and Groq clients."""
        # Initialize Cohere for re-ranking
        if settings.cohere_api_key:
            self.cohere_client = cohere.Client(settings.cohere_api_key)
        else:
            self.cohere_client = None
            logger.warning("Cohere API key not provided, re-ranking will be disabled")
        
        # Initialize Groq for LLM analysis
        if settings.groq_api_key:
            self.groq_client = Groq(api_key=settings.groq_api_key)
        else:
            self.groq_client = None
            logger.warning("Groq API key not provided, LLM analysis will be disabled")
        
        self.vector_store = get_vector_store()
        logger.info("Initialized NewsRecommender")
    
    def get_recommendations(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Get news recommendations based on a query.
        
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
            
            # Add AI insights if Groq is available
            if self.groq_client:
                final_recommendations = self._add_ai_insights(query, final_recommendations)
            
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
    
    def _add_ai_insights(self, query: str, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add AI-generated insights to recommended articles.
        
        Args:
            query: Original query
            articles: List of recommended articles
            
        Returns:
            Articles with AI insights added
        """
        try:
            logger.info("Adding AI insights to recommendations")
            
            # Create a summary of all articles for context
            articles_summary = "\n".join([
                f"- {article['title']}: {article['summary'][:100]}..."
                for article in articles[:5]  # Limit to top 5 for context
            ])
            
            prompt = f"""
            Based on the user query: "{query}"
            
            Here are the top recommended news articles:
            {articles_summary}
            
            Provide a brief insight (2-3 sentences) about why these articles are relevant to the user's interest and what key themes or trends they represent.
            """
            
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": "You are a helpful news analyst that provides insights about news recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.max_tokens,
                temperature=settings.temperature
            )
            
            ai_insight = response.choices[0].message.content
            
            # Add insight to the first article or as a separate field
            if articles:
                articles[0]['ai_insight'] = ai_insight
            
            logger.info("Successfully added AI insights")
            return articles
            
        except Exception as e:
            logger.error(f"Error adding AI insights: {str(e)}")
            # Return articles without insights if AI analysis fails
            return articles
    
    def get_similar_articles(self, article_id: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Get articles similar to a specific article by ID.

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

            # Get the source article
            source_article = self.vector_store.get_article_by_id(article_id)
            if not source_article:
                logger.warning(f"Article with ID {article_id} not found")
                return []

            # Create query from article title and content
            query_text = f"{source_article['title']} {source_article.get('summary', '')}"
            logger.info(f"Using query text: {query_text[:100]}...")

            # Get similar articles using the existing recommendation logic
            # Request more results to account for filtering out the source article
            similar_articles = self.get_recommendations(
                query=query_text,
                max_results=max_results + 1  # +1 to account for source article removal
            )

            # Filter out the source article from recommendations
            filtered_articles = [
                article for article in similar_articles
                if article.get('id') != article_id
            ]

            # Limit to requested number of results
            final_results = filtered_articles[:max_results]

            logger.info(f"Returning {len(final_results)} similar articles for article {article_id}")
            return final_results

        except Exception as e:
            logger.error(f"Error getting similar articles for {article_id}: {str(e)}")
            raise

    def get_trending_topics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Analyze trending topics from recent articles.
        
        Args:
            limit: Number of trending topics to return
            
        Returns:
            List of trending topics with analysis
        """
        try:
            logger.info("Analyzing trending topics")
            
            # Get recent articles (this is a simplified approach)
            # In a real implementation, you might want to filter by date
            recent_articles = self.vector_store.search_similar_articles(
                query="news today current events",
                n_results=50
            )
            
            if not recent_articles or not self.groq_client:
                return []
            
            # Create summary of recent articles
            articles_text = "\n".join([
                f"- {article['title']}"
                for article in recent_articles[:20]
            ])
            
            prompt = f"""
            Analyze these recent news headlines and identify the top {limit} trending topics or themes:
            
            {articles_text}
            
            For each trending topic, provide:
            1. Topic name
            2. Brief description (1-2 sentences)
            3. Why it's trending
            
            Format as a JSON list with objects containing: topic, description, reason
            """
            
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": "You are a news analyst that identifies trending topics. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.max_tokens,
                temperature=0.3
            )
            
            # Parse the response (simplified - in production, add better error handling)
            import json
            try:
                trending_topics = json.loads(response.choices[0].message.content)
                logger.info(f"Identified {len(trending_topics)} trending topics")
                return trending_topics
            except json.JSONDecodeError:
                logger.error("Failed to parse trending topics JSON response")
                return []
            
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
