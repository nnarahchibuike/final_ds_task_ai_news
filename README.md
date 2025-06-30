# DS Task AI News

DS Task AI News is an AI-powered news retrieval API that gathers news articles from various online sources, stores them in a vector database, and provides intelligent news recommendations. The system uses advanced AI techniques to find and recommend related news articles through a clean REST API.

## Features

- **News Aggregation**: Fetches news using categorized RSS feeds (Mainstream News, Music, Gaming, Tech, Lifestyle)
- **Vector Database Storage**: Stores news articles in Pinecone for efficient similarity searches
- **AI-powered Recommendations**: Uses Cohere embeddings to provide relevant news recommendations
- **Clean Web Interface**: Modern, responsive frontend with glassmorphism design
- **FastAPI Backend**: Clean REST API with automatic documentation and static file serving
- **Background Processing**: Asynchronous news fetching and vector storage
- **Unified Application**: Frontend and backend served from single command
- **Scalable Architecture**: Designed for easy integration and deployment

## Quick Start

### Prerequisites

- Python 3.8 or higher
- API keys for [Cohere](https://dashboard.cohere.ai/), [Groq](https://console.groq.com/), and [Pinecone](https://app.pinecone.io/)

### Installation

1. **Clone and setup:**

   ```bash
   git clone <repository-url>
   cd ds_task_ai_news
   ./setup.sh  # On Windows: setup.bat
   ```

2. **Configure API keys:**
   Edit `.env` file and add your API keys:

   ```env
   COHERE_API_KEY=your_cohere_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   ```

3. **Run the application:**

   ```bash
   # Option 1: Simple startup (recommended)
   python start_app.py

   # Option 2: Use the management script
   python run_pipeline.py

   # Option 3: Manual steps
   # Step 1: Run the preprocessing pipeline
   python pipeline.py

   # Step 2: Start the API server and frontend
   python backend/main.py
   ```

4. **Access the API:**
   - **API Server**: http://localhost:8000
   - **Interactive Documentation**: http://localhost:8000/docs
   - **Alternative Documentation**: http://localhost:8000/redoc

## New Workflow: Standalone Pipeline

This system now uses a **standalone preprocessing pipeline** that runs independently before the API:

### Pipeline Commands

```bash
# Run complete workflow (pipeline + API)
python run_pipeline.py

# Run only the preprocessing pipeline
python run_pipeline.py --pipeline

# Start only the API (requires processed data)
python run_pipeline.py --api

# Check system status
python run_pipeline.py --status

# Clean old data files
python run_pipeline.py --clean
```

### Pipeline Process

1. **Raw News Fetching**: Collects articles from RSS feeds
2. **AI Enhancement**: Uses Groq LLM for summaries and metadata
3. **Vector Storage**: Generates embeddings and stores in Pinecone
4. **API Output**: Creates processed files for fast API responses

## API Endpoints

### Core Endpoints

- `GET /fetch-news` - Load processed news articles from pipeline output
- `GET /recommend-news?article_id={id}&max_results={n}` - Get news recommendations based on an article ID

**Note**: The `/fetch-news` endpoint now reads from pre-processed files. To get fresh articles, run the pipeline first.

### Documentation

- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

### Example Usage

**Load Processed News:**
```bash
curl -X GET "http://localhost:8000/fetch-news"
```

**Get Recommendations:**
```bash
curl -X GET "http://localhost:8000/recommend-news?article_id=bbc_abc123&max_results=5"
```

**Complete Workflow Example:**
```bash
# 1. Run the preprocessing pipeline
python pipeline.py

# 2. Start the API server
python backend/main.py

# 3. Load processed articles
curl -X GET "http://localhost:8000/fetch-news"

# 4. Get recommendations for an article
curl -X GET "http://localhost:8000/recommend-news?article_id=<article_id>&max_results=5"
```

## Project Structure

```
DS_Task_AI_News/
├── pipeline.py             # NEW: Standalone preprocessing pipeline
├── run_pipeline.py         # NEW: Pipeline management script
├── backend/
│   ├── main.py              # MODIFIED: FastAPI backend (reads processed data)
│   ├── news_fetcher.py      # USED BY: Pipeline for RSS fetching
│   ├── news_processor.py    # USED BY: Pipeline for AI enhancement
│   ├── vector_store.py      # USED BY: Both pipeline and API
│   ├── embeddings.py        # USED BY: Pipeline for embeddings
│   ├── recommender.py       # USED BY: API for recommendations
│   ├── config.py            # SHARED: Configuration settings
│   ├── requirements.txt     # Dependencies
│   └── debug_rss.py         # RSS debugging utility
├── data/
│   ├── raw_news/           # CREATED BY: Pipeline (raw articles)
│   └── processed_news/     # CREATED BY: Pipeline, READ BY: API
├── docs/
│   ├── README.md           # Documentation for new developers
│   └── API_Documentation.md # API details
├── rss.py                  # RSS feed processing module
├── setup.sh / setup.bat    # Setup scripts
├── run.sh / run.bat        # Run scripts
├── .env                    # Environment variables
├── .gitignore              # Git ignore file
└── LICENSE                 # License information
```

## Getting Started

### 1. Initial Setup
After installation, test your setup:
```bash
python test_setup.py
```

### 2. Fetch Your First News Articles
```bash
curl -X GET "http://localhost:8000/fetch-news"
```

### 3. Get Recommendations
Use an article ID from the fetch response:
```bash
curl -X GET "http://localhost:8000/recommend-news?article_id=bbc_abc123&max_results=5"
```

## Documentation

- [API Documentation](docs/API_Documentation.md) - Complete API reference
- [Interactive API Docs](http://localhost:8000/docs) - When running locally
- [Alternative API Docs](http://localhost:8000/redoc) - ReDoc interface

## Technologies Used

- **FastAPI** - Modern Python web framework for APIs
- **Pinecone** - Vector database for similarity search
- **Cohere** - AI embeddings for semantic search
- **Groq** - Fast LLM inference (optional)
- **Loguru** - Advanced logging
- **Pydantic** - Data validation and settings management
- **Uvicorn** - ASGI server for production deployment

## Configuration

The system uses environment variables for configuration. Key settings include:

- **API Keys**: Cohere, Groq, and Pinecone API keys
- **Database Settings**: Pinecone index name and namespace
- **News Sources**: RSS feed URLs organized by category
- **Processing Settings**: Embedding models, similarity thresholds

See `.env.example` for all available configuration options.

## Development

### Running Tests
```bash
python test_setup.py
```

### Adding New RSS Feeds
Edit `backend/config.py` and add feeds to the `rss_feeds` dictionary:
```python
"new_category": [
    "https://example.com/rss.xml"
]
```

### Debugging RSS Feeds
Use the debug utility to test RSS feed parsing:
```bash
cd backend
python debug_rss.py
```

## Deployment

The API is ready for deployment using any ASGI server:

```bash
# Production deployment
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `python test_setup.py`
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions or issues:
- Check the [API Documentation](docs/API_Documentation.md)
- Review the interactive docs at http://localhost:8000/docs
- Create an issue in the repository
