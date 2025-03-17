# DS Task AI News

## Project Overview

DS Task AI News is an AI-powered news retrieval system that gathers news articles from various online sources, stores them in a vector database, and enables users to discover relevant articles based on their interests. The system uses advanced AI techniques to find and recommend related news articles dynamically.

## Features

* **News Aggregation** : Fetches news using RSS feeds from various online portals.
* **Vector Database Storage** : Stores news articles in a vector database for efficient similarity searches.
* **AI-powered Recommendations** : Uses Cohere embeddings and re-ranking to provide relevant news recommendations.
* **LLM-powered Analysis** : Utilizes Groq for AI-driven insights and processing.

## Tech Stack

* **LLM** : Groq
* **Search** : RSS Feeds for news aggregation
* **Embeddings & Re-Ranking** : Cohere
* **Vector Database** : (e.g., Pinecone, Weaviate, or FAISS)
* **Backend** : FastAPI

## File Structure

```
DS_Task_AI_News/
│-- backend/
│   │-- main.py  # FastAPI backend
│   │-- news_fetcher.py  # Fetches news using RSS feeds
│   │-- vector_store.py  # Handles vector database operations
│   │-- embeddings.py  # Generates embeddings using Cohere
│   │-- recommender.py  # Fetches related news articles
│   │-- config.py  # Configuration settings
│   │-- requirements.txt  # Dependencies
│
│-- data/
│   │-- raw_news/  # Stores raw news articles before processing
│   │-- processed_news/  # Stores cleaned and processed articles
│
│-- docs/
│   │-- README.md  # Documentation for new developers
│   │-- API_Documentation.md  # API details
│
│-- .env  # Environment variables
│-- .gitignore  # Git ignore file
│-- LICENSE  # License information
```

## Setup & Installation

### 1. Clone the Repository

```bash
git clone http://23.29.118.76:3000/Test/ds_task_ai_news
cd ds-task-ai-news
```

### 2. Set Up the Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

## Fetching News Using RSS Feeds

* News is aggregated from RSS feeds of different news sources.
* The `news_fetcher.py` script pulls data from RSS feeds, extracts relevant information, and stores it in the database.

### **Example RSS Fetching Code (Python)**

```python
import feedparser

def fetch_rss_news(feed_url):
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries:
        articles.append({
            "title": entry.title,
            "content": entry.summary,
            "date": entry.published,
            "slug": entry.title.lower().replace(" ", "-"),
            "categories": ["Technology", "AI and Innovation"],
            "tags": ["AI", "Technology", "Innovation"]
        })
    return articles
```

## API Endpoints

* `GET /fetch-news`: Fetches news from RSS feeds.
* `GET /recommend-news?article_id=xyz`: Retrieves similar news based on the selected article.
