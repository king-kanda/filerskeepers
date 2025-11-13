"""FastAPI application main entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from src.api.routes import router
from src.api.rate_limiter import limiter, rate_limit_exceeded_handler
from src.database.mongodb import db
from src.utils.config import settings
from src.utils.logger import log


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    log.info("Starting up FastAPI application...")
    await db.connect()
    log.info("Application started successfully")

    yield

    # Shutdown
    log.info("Shutting down FastAPI application...")
    await db.disconnect()
    log.info("Application shut down successfully")


# Create FastAPI application
app = FastAPI(
    title="Books Scraper API",
    description="""
    # Books Scraper API

    A production-grade web scraping and API system for monitoring book data from books.toscrape.com.

    ## Features

    * **Web Crawling**: Async web crawler with retry logic and resume capability
    * **Change Detection**: Automated monitoring and detection of book data changes
    * **RESTful API**: Secure API with authentication and rate limiting
    * **Data Storage**: Efficient MongoDB storage with indexing
    * **Scheduling**: Daily automated crawls with APScheduler

    ## Authentication

    All API endpoints require an API key. Include your API key in the `X-API-Key` header:

    ```
    X-API-Key: your-api-key-here
    ```

    ## Rate Limiting

    API requests are rate-limited to {rate_limit} requests per hour per API key.

    ## Endpoints

    * `GET /api/v1/books` - Get books with filtering and pagination
    * `GET /api/v1/books/{{book_id}}` - Get a specific book by ID
    * `GET /api/v1/changes` - Get recent changes and updates

    """.format(rate_limit=settings.rate_limit_per_hour),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add rate limiter state
app.state.limiter = limiter

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

# Exception handlers
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.

    Args:
        request: FastAPI request object
        exc: Exception that was raised

    Returns:
        JSON error response
    """
    log.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
        })


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Books Scraper API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/api/v1/health",
        "status": "running"
    }


@app.get("/api/v1/stats", tags=["system"])
async def get_stats():
    """Get basic statistics about the database."""
    try:
        total_books = await db.count_books()
        total_changes = await db.count_change_logs()
        last_crawl = await db.get_last_crawl_status()

        return {
            "total_books": total_books,
            "total_changes": total_changes,
            "last_crawl": last_crawl,
        }
    except Exception as e:
        log.error(f"Error fetching stats: {e}")
        return JSONResponse(status_code=500,
                            content={"error": "Failed to fetch statistics"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.main:app",
                host=settings.api_host,
                port=settings.api_port,
                reload=True,
                log_level=settings.log_level.lower())
