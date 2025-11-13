"""Script to run the FastAPI server."""
import uvicorn
from src.utils.config import settings
from src.utils.logger import log


def main():
    """Main entry point for API server."""
    try:
        log.info("=" * 60)
        log.info("Starting Books Scraper API")
        log.info(f"Host: {settings.api_host}")
        log.info(f"Port: {settings.api_port}")
        log.info(f"Documentation: http://{settings.api_host}:{settings.api_port}/docs")
        log.info("=" * 60)

        uvicorn.run(
            "src.api.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=False,
            log_level=settings.log_level.lower()
        )

    except KeyboardInterrupt:
        log.info("API server interrupted by user")
    except Exception as e:
        log.error(f"API server failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
