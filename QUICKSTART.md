# Quick Start Guide

Get up and running with Books Scraper in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- OR Python 3.11+ and MongoDB 7.0+

## 🚀 Docker Quick Start (Recommended)

### 1. Start the System

```bash
# Start MongoDB and API server
docker-compose up -d

# Check if services are running
docker-compose ps
```

### 2. Run the Crawler

```bash
# Run a one-time crawl
docker-compose --profile crawler up crawler

# Watch the logs
docker-compose logs -f crawler
```

### 3. Access the API

Open your browser and go to:
- **Swagger UI**: http://localhost:8000/docs
- **API Root**: http://localhost:8000

### 4. Test API Endpoints

Use the API key from `.env` file (default: `dev-key-1`)

```bash
# Get all books
curl -X GET "http://localhost:8000/api/v1/books" \
  -H "X-API-Key: dev-key-1"

# Get books by category
curl -X GET "http://localhost:8000/api/v1/books?category=Fiction" \
  -H "X-API-Key: dev-key-1"

# Get recent changes
curl -X GET "http://localhost:8000/api/v1/changes" \
  -H "X-API-Key: dev-key-1"
```

### 5. Optional: Start Scheduler

```bash
# Start automated daily crawls
docker-compose --profile scheduler up -d scheduler

# View scheduler logs
docker-compose logs -f scheduler
```

## 🐍 Local Python Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 2. Start MongoDB

```bash
# macOS with Homebrew
brew services start mongodb-community@7.0

# Ubuntu/Debian
sudo systemctl start mongod

# Or use Docker
docker run -d -p 27017:27017 --name mongodb mongo:7.0
```

### 3. Run Crawler

```bash
python run_crawler.py
```

### 4. Start API Server

```bash
# In a new terminal
python run_api.py

# Or with uvicorn directly
uvicorn src.api.main:app --reload
```

### 5. Access the API

- **Swagger UI**: http://localhost:8000/docs
- **API Root**: http://localhost:8000

## 📊 Import Postman Collection

1. Open Postman
2. Click **Import**
3. Select `postman_collection.json`
4. Set the `api_key` variable to `dev-key-1`
5. Start testing!

## 🧪 Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🔑 Default Configuration

- **API URL**: http://localhost:8000
- **API Keys**: `dev-key-1`, `dev-key-2`
- **MongoDB**: mongodb://localhost:27017
- **Database**: books_scraper
- **Rate Limit**: 100 requests/hour

## 📝 Common Commands

### Docker

```bash
# Stop all services
docker-compose down

# View logs
docker-compose logs -f api

# Rebuild containers
docker-compose build

# Remove all data (including database)
docker-compose down -v
```

### Local Development

```bash
# Run crawler
python run_crawler.py

# Run API server
python run_api.py

# Run scheduler
python run_scheduler.py

# Run tests
pytest

# Format code
black src/ tests/
```

## 🆘 Troubleshooting

### Port 8000 already in use

```bash
# Change port in .env
API_PORT=8001

# Or stop the service using port 8000
lsof -ti:8000 | xargs kill -9
```

### MongoDB connection error

```bash
# Check if MongoDB is running
docker-compose ps mongodb

# Or for local MongoDB
brew services list | grep mongodb  # macOS
systemctl status mongod  # Linux
```

### API returns 401 Unauthorized

- Check that you're including the `X-API-Key` header
- Verify the API key matches one in your `.env` file

### Crawler fails to connect

- Check internet connection
- Verify the target website is accessible
- Check logs in `logs/app.log`

## 📖 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the [API documentation](http://localhost:8000/docs)
- Check the `reports/` folder for change reports
- Review `logs/app.log` for detailed logs

## 🎉 You're Ready!

The system is now running and ready to:
- ✅ Crawl books from books.toscrape.com
- ✅ Store data in MongoDB
- ✅ Serve data via REST API
- ✅ Detect and log changes
- ✅ Generate reports

For more details, see [README.md](README.md)
