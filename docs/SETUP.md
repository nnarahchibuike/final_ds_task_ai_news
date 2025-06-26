# DS Task AI News - Setup Guide

This guide will help you set up the DS Task AI News backend API service.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- API keys for:
  - Cohere (for embeddings)
  - Groq (for LLM analysis - optional)
  - Pinecone (for vector database)

## Quick Installation

### Option 1: Automated Setup (Recommended)

```bash
git clone <repository-url>
cd ds_task_ai_news
./setup.sh  # On Windows: setup.bat
```

### Option 2: Manual Setup

1. **Clone the Repository**

```bash
git clone <repository-url>
cd ds_task_ai_news
```

2. **Create Virtual Environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**

```bash
cd backend
pip install -r requirements.txt
cd ..
```

4. **Configure Environment Variables**

```bash
cp .env.example .env
```

Edit `.env` file and add your API keys:

```env
COHERE_API_KEY=your_cohere_api_key_here
GROQ_API_KEY=your_groq_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
```

## Getting API Keys

### Cohere API Key

1. Visit [Cohere Dashboard](https://dashboard.cohere.ai/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

### Groq API Key

1. Visit [Groq Console](https://console.groq.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

### Pinecone API Key

1. Visit [Pinecone Console](https://app.pinecone.io/)
2. Sign up or log in
3. Create a new project or use existing one
4. Navigate to API Keys section
5. Copy your API key to your `.env` file
6. Note: The new Pinecone API uses serverless indexes by default, no environment configuration needed

## Running the API Server

### Start the Server

**Option 1: Using run script (Recommended)**

```bash
./run.sh  # On Windows: run.bat
```

**Option 2: Manual start**

```bash
cd backend
python main.py
```

**Option 3: Using uvicorn directly**

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Access the API

- **API Server**: http://localhost:8000
- **Interactive Documentation**: http://localhost:8000/docs
- **Alternative Documentation**: http://localhost:8000/redoc

## Initial Setup and Testing

### 1. Verify Installation

Test that everything is working:

```bash
python test_setup.py
```

### 2. Fetch Initial News Data

```bash
curl -X GET "http://localhost:8000/fetch-news"
```

### 3. Test Recommendations

Use an article ID from the fetch response:

```bash
curl -X GET "http://localhost:8000/recommend-news?article_id=bbc_abc123&max_results=5"
```

### 4. Explore the API

Visit the interactive documentation:
- http://localhost:8000/docs

## Configuration Options

All configuration options can be set via environment variables in the `.env` file:

### Database Settings

- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_INDEX_NAME`: Name of the Pinecone index (default: "news-articles")
- `PINECONE_NAMESPACE`: Namespace within the index (default: "default")
- `RAW_NEWS_DIR`: Directory for raw news data
- `PROCESSED_NEWS_DIR`: Directory for processed news data

### API Settings

- `API_HOST`: Server host (default: 0.0.0.0)
- `API_PORT`: Server port (default: 8000)
- `API_RELOAD`: Enable auto-reload in development

### News Fetching

- `FETCH_INTERVAL_HOURS`: How often to fetch news
- `MAX_ARTICLES_PER_FEED`: Maximum articles per RSS feed

### AI Settings

- `EMBEDDING_MODEL`: Cohere embedding model
- `GROQ_MODEL`: Groq LLM model
- `MAX_TOKENS`: Maximum tokens for LLM responses
- `TEMPERATURE`: LLM temperature setting

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed and virtual environment is activated
2. **API Key Errors**: Verify API keys are correctly set in `.env` file
3. **Database Errors**: Check that data directories exist and are writable
4. **Network Errors**: Ensure internet connection for RSS feeds and API calls

### Logs

The application uses loguru for logging. Check console output for detailed error messages.

### Database Issues

Check Pinecone connection and ensure your API key is valid. The system will create the index automatically if it doesn't exist.

## Development

### Running Tests

```bash
python test_setup.py
```

### Code Structure

- `backend/main.py`: FastAPI application and API routes
- `backend/config.py`: Configuration management
- `backend/news_fetcher.py`: RSS feed fetching
- `backend/vector_store.py`: Pinecone vector database operations
- `backend/embeddings.py`: Cohere embedding generation
- `backend/recommender.py`: AI-powered recommendations
- `backend/debug_rss.py`: RSS debugging utility

### Adding New RSS Feeds

RSS feeds are organized by categories in `config.py`. To add new feeds:

1. Edit the `rss_feeds` dictionary in `config.py`
2. Add feeds to existing categories or create new categories
3. Available categories: mainstream_news, music, gaming, tech, lifestyle

Example:

```python
rss_feeds: Dict[str, List[str]] = {
    "tech": [
        "https://www.wired.com/feed/rss",
        "https://your-new-tech-feed.com/rss"  # Add new feed here
    ],
    "your_new_category": [  # Add new category
        "https://example.com/rss"
    ]
}
```
