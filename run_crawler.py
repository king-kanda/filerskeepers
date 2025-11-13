"""Script to run the web crawler."""
import asyncio
import sys
from src.crawler.scraper import run_scraper
from src.utils.logger import log


async def main():
    """Main entry point for crawler."""
    try:
        log.info("=" * 60)
        log.info("Starting Books Scraper")
        log.info("=" * 60)

        # Run the scraper
        stats = await run_scraper(resume=True)

        log.info("=" * 60)
        log.info("Crawl Summary:")
        log.info(f"  Total Books: {stats['total_books']}")
        log.info(f"  New Books: {stats['new_books']}")
        log.info(f"  Updated Books: {stats['updated_books']}")
        log.info(f"  Failed Pages: {stats['failed_pages']}")
        log.info("=" * 60)

        return 0

    except KeyboardInterrupt:
        log.info("Crawler interrupted by user")
        return 1
    except Exception as e:
        log.error(f"Crawler failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
