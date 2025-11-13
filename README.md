# Books Scraper - Production-Grade Web Scraping & API System

A comprehensive, production-ready web scraping and API system for monitoring and serving book data from [books.toscrape.com](https://books.toscrape.com). Built with modern Python technologies including FastAPI, MongoDB, and async programming.

## 🚀 Features

### Part 1: Robust & Scalable Crawler
- ✅ Async web crawling with `httpx` for high performance
- ✅ Automatic retry logic with exponential backoff
- ✅ Resume capability from last successful crawl
- ✅ Pagination handling and error recovery
- ✅ Pydantic schema validation
- ✅ Raw HTML snapshot storage for fallback
- ✅ Efficient MongoDB storage with indexing
- ✅ Comprehensive logging and progress tracking

### Part 2: Scheduler & Change Detection
- ✅ APScheduler for automated daily crawls
- ✅ Intelligent change detection with content hashing
- ✅ Detailed change log tracking (price, availability, rating, reviews)
- ✅ Automated report generation (JSON/CSV)
- ✅ Email alerts for significant changes
- ✅ Configurable scheduling

### Part 3: Secure RESTful API
- ✅ FastAPI with automatic OpenAPI/Swagger documentation
- ✅ API key-based authentication
- ✅ Rate limiting (100 requests/hour by default)
- ✅ Advanced filtering (category, price range, rating)
- ✅ Pagination support
- ✅ Change tracking endpoint
- ✅ Health check endpoint

## 📋 Requirements

- **Python**: 3.11+
- **MongoDB**: 7.0+
- **Docker** (optional): 20.10+
- **Docker Compose** (optional): 2.0+

## 🏗️ Project Structure

```
books-scraper/
├── src/
│   ├── crawler/          # Web scraping components
│   │   ├── scraper.py    # Main crawler logic
│   │   ├── parser.py     # HTML parsing utilities
│   │   └── retry.py      # Retry logic with exponential backoff
│   ├── database/         # Database layer
│   │   └── mongodb.py    # MongoDB operations
│   ├── scheduler/        # Scheduling & change detection
│   │   ├── scheduler.py  # APScheduler setup
│   │   └── change_detector.py  # Change detection logic
│   ├── api/              # FastAPI application
│   │   ├── main.py       # FastAPI app setup
│   │   ├── routes.py     # API endpoints
│   │   ├── auth.py       # Authentication
│   │   └── rate_limiter.py  # Rate limiting
│   ├── schemas/          # Pydantic models
│   │   └── book.py       # Book schemas
│   └── utils/            # Utilities
│       ├── config.py     # Configuration management
│       └── logger.py     # Logging setup
├── tests/                # Test suite
│   ├── test_crawler.py
│   ├── test_api.py
│   └── test_change_detection.py
├── docker/               # Docker configuration
├── logs/                 # Application logs
├── reports/              # Generated reports
├── .env.example          # Example environment variables
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Docker image definition
├── run_crawler.py        # Crawler entry point
├── run_scheduler.py      # Scheduler entry point
├── run_api.py            # API server entry point
└── README.md             # This file
```

## 🚀 Quick Start

### Option 1: Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd books-scraper
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the services**
   ```bash
   # Start MongoDB and API server
   docker-compose up -d

   # Run the crawler (one-time)
   docker-compose --profile crawler up crawler

   # Or start the scheduler for automated daily crawls
   docker-compose --profile scheduler up -d scheduler
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Swagger Documentation: http://localhost:8000/docs
   - ReDoc Documentation: http://localhost:8000/redoc

### Option 2: Local Development

1. **Install Python 3.11+**
   ```bash
   python --version  # Ensure 3.11 or higher
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install and start MongoDB**
   ```bash
   # On macOS with Homebrew
   brew tap mongodb/brew
   brew install mongodb-community@7.0
   brew services start mongodb-community@7.0

   # On Ubuntu/Debian
   sudo apt-get install -y mongodb-org
   sudo systemctl start mongod

   # On Windows
   # Download and install from https://www.mongodb.com/try/download/community
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Run the crawler**
   ```bash
   python run_crawler.py
   ```

7. **Start the API server**
   ```bash
   python run_api.py
   # Or with uvicorn directly:
   uvicorn src.api.main:app --reload
   ```

8. **Optional: Start the scheduler**
   ```bash
   python run_scheduler.py
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=books_scraper

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_KEYS=your-api-key-1,your-api-key-2

# Rate Limiting
RATE_LIMIT_PER_HOUR=100

# Crawler Configuration
TARGET_URL=https://books.toscrape.com
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=2

# Scheduler Configuration
CRAWL_SCHEDULE_HOUR=2
CRAWL_SCHEDULE_MINUTE=0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Email Alerts (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL=alerts@example.com
```

## 📚 API Documentation

### Authentication

All API endpoints require an API key. Include it in the request header:

```bash
X-API-Key: your-api-key-here
```

### Endpoints

#### 1. Get Books with Filtering

```http
GET /api/v1/books?category=Fiction&min_price=10&max_price=50&rating=Four&sort_by=-price&page=1&page_size=20
```

**Query Parameters:**
- `category` (optional): Filter by book category
- `min_price` (optional): Minimum price (inclusive)
- `max_price` (optional): Maximum price (inclusive)
- `rating` (optional): Filter by rating (One, Two, Three, Four, Five)
- `sort_by` (optional): Sort field (price, rating, reviews). Prefix with `-` for descending
- `page` (default: 1): Page number
- `page_size` (default: 20, max: 100): Items per page

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/books?category=Fiction&rating=Five" \
  -H "X-API-Key: dev-key-1"
```

**Response:**
```json
{
  "items": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "A Light in the Attic",
      "description": "It's hard to imagine...",
      "category": "Poetry",
      "price_excl_tax": 51.77,
      "price_incl_tax": 51.77,
      "availability": "In stock (22 available)",
      "num_reviews": 0,
      "image_url": "http://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg",
      "rating": "Three",
      "source_url": "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
      "crawl_timestamp": "2025-11-12T10:30:00",
      "last_updated": "2025-11-12T10:30:00"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

#### 2. Get Book by ID

```http
GET /api/v1/books/{book_id}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/books/507f1f77bcf86cd799439011" \
  -H "X-API-Key: dev-key-1"
```

#### 3. Get Recent Changes

```http
GET /api/v1/changes?change_type=price_change&page=1&page_size=50
```

**Query Parameters:**
- `book_id` (optional): Filter by book ID
- `change_type` (optional): Filter by change type (new_book, price_change, availability_change, etc.)
- `page` (default: 1): Page number
- `page_size` (default: 50, max: 100): Items per page

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/changes?change_type=price_change" \
  -H "X-API-Key: dev-key-1"
```

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439012",
    "book_id": "507f1f77bcf86cd799439011",
    "book_name": "A Light in the Attic",
    "change_type": "price_change",
    "old_value": "55.00",
    "new_value": "51.77",
    "detected_at": "2025-11-12T10:30:00",
    "details": {
      "old_price_excl_tax": 55.0,
      "new_price_excl_tax": 51.77
    }
  }
]
```

#### 4. Health Check

```http
GET /api/v1/health
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

#### 5. Statistics

```http
GET /api/v1/stats
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/stats"
```

### Interactive API Documentation

Visit these URLs when the API server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

### Run All Tests

```bash
# Using pytest
pytest

# With coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_crawler.py

# Run specific test
pytest tests/test_api.py::TestBooksEndpoint::test_get_books_with_filters
```

### Test Coverage

The test suite includes:
- Unit tests for HTML parsing
- Unit tests for change detection
- API endpoint tests
- Integration tests for crawler functionality

## 📊 Database Schema

### Books Collection

```javascript
{
  "_id": ObjectId,
  "name": String,
  "description": String,
  "category": String,
  "price_excl_tax": Float,
  "price_incl_tax": Float,
  "availability": String,
  "num_reviews": Integer,
  "image_url": String,
  "rating": String,
  "source_url": String (unique),
  "raw_html": String,
  "content_hash": String,
  "crawl_timestamp": DateTime,
  "last_updated": DateTime,
  "created_at": DateTime
}
```

**Indexes:**
- `source_url` (unique)
- `content_hash`
- `category`
- `price_incl_tax`
- `rating`
- `num_reviews`
- Compound: `(category, price_incl_tax)`

### Change Logs Collection

```javascript
{
  "_id": ObjectId,
  "book_id": String,
  "book_name": String,
  "change_type": String,
  "old_value": String,
  "new_value": String,
  "detected_at": DateTime,
  "details": Object
}
```

**Indexes:**
- `book_id`
- `change_type`
- `detected_at` (descending)

## 🔧 Advanced Usage

### Manual Crawler Run

```bash
# Basic crawl
python run_crawler.py

# With Docker
docker-compose --profile crawler up crawler
```

### Scheduler Configuration

The scheduler runs daily crawls at a configured time (default: 2:00 AM). Configure in `.env`:

```bash
CRAWL_SCHEDULE_HOUR=2
CRAWL_SCHEDULE_MINUTE=0
```

### Email Alerts

Configure SMTP settings in `.env` to receive email alerts:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use app-specific password for Gmail
ALERT_EMAIL=alerts@example.com
```

### Change Reports

Reports are automatically generated in `reports/` directory:
- JSON format: `change_report_YYYYMMDD_HHMMSS.json`
- CSV format: `change_report_YYYYMMDD_HHMMSS.csv`

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f mongodb

# Stop all services
docker-compose down

# Rebuild containers
docker-compose build --no-cache

# Run crawler once
docker-compose --profile crawler up crawler

# Start scheduler
docker-compose --profile scheduler up -d scheduler

# Execute command in container
docker-compose exec api python run_crawler.py

# Access MongoDB shell
docker-compose exec mongodb mongosh books_scraper
```

## 📝 Logging

Logs are written to:
- Console (with colors)
- File: `logs/app.log` (with rotation)

Configure log level in `.env`:
```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🔒 Security Considerations

1. **API Keys**: Use strong, unique API keys in production
2. **Environment Variables**: Never commit `.env` files
3. **MongoDB**: Enable authentication in production
4. **CORS**: Configure allowed origins appropriately
5. **Rate Limiting**: Adjust limits based on your needs
6. **HTTPS**: Use reverse proxy (nginx) with SSL in production

## 🚀 Production Deployment

### Recommended Setup

1. **Use Docker Compose** with proper resource limits
2. **Enable MongoDB authentication**
3. **Use nginx as reverse proxy** with SSL/TLS
4. **Configure firewall** to restrict MongoDB access
5. **Set up monitoring** (Prometheus, Grafana)
6. **Configure log aggregation** (ELK stack)
7. **Set up automated backups** for MongoDB

### Example nginx Configuration

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📄 License

This project is for educational and demonstration purposes.

## 👥 Author

Created as a production-grade solution for web scraping and API development.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📞 Support

For issues and questions:
- Check the [documentation](#-api-documentation)
- Review logs in `logs/app.log`
- Open an issue on GitHub

---

**Happy Scraping! 🎉**
