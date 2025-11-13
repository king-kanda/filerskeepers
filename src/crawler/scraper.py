"""Main web scraper with async operations and resume capability."""
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from src.crawler.parser import BookParser
from src.crawler.retry import RetryableHTTPClient
from src.database.mongodb import db
from src.schemas.book import BookCreate, CrawlStatus
from src.utils.config import settings
from src.utils.logger import log


class BookScraper:
    """Async web scraper for books.toscrape.com with resume capability."""

    def __init__(self, base_url: str = None):
        """
        Initialize the scraper.

        Args:
            base_url: Base URL to scrape (defaults to settings)
        """
        self.base_url = base_url or settings.target_url
        self.parser = BookParser()
        self.progress_file = Path("scraper_progress.json")
        self.stats = {
            "total_books": 0,
            "new_books": 0,
            "updated_books": 0,
            "failed_pages": 0,
            "processed_urls": set(),
        }

    async def crawl(self, resume: bool = True) -> Dict[str, Any]:
        """
        Crawl all books from the website.

        Args:
            resume: Whether to resume from last checkpoint

        Returns:
            Dictionary with crawl statistics
        """
        crawl_started = datetime.utcnow()
        log.info(f"Starting crawl of {self.base_url}")

        # Load progress if resuming
        if resume:
            self._load_progress()

        try:
            # Connect to database
            await db.connect()

            # Start crawling
            async with RetryableHTTPClient() as client:
                await self._crawl_catalog(client)

            crawl_finished = datetime.utcnow()

            # Save final status
            status = CrawlStatus(
                total_books=self.stats["total_books"],
                new_books=self.stats["new_books"],
                updated_books=self.stats["updated_books"],
                failed_pages=self.stats["failed_pages"],
                crawl_started=crawl_started,
                crawl_finished=crawl_finished,
                status="completed"
            )

            await db.save_crawl_status(status.model_dump())

            log.info(
                f"Crawl completed: {self.stats['total_books']} books processed, "
                f"{self.stats['new_books']} new, {self.stats['updated_books']} updated, "
                f"{self.stats['failed_pages']} failed"
            )

            # Clean up progress file on success
            if self.progress_file.exists():
                self.progress_file.unlink()

            return self.stats

        except Exception as e:
            log.error(f"Crawl failed: {e}")
            crawl_finished = datetime.utcnow()

            # Save error status
            status = CrawlStatus(
                total_books=self.stats["total_books"],
                new_books=self.stats["new_books"],
                updated_books=self.stats["updated_books"],
                failed_pages=self.stats["failed_pages"],
                crawl_started=crawl_started,
                crawl_finished=crawl_finished,
                status="failed",
                error_message=str(e)
            )

            await db.save_crawl_status(status.model_dump())

            # Save progress for resume
            self._save_progress()

            raise

        finally:
            await db.disconnect()

    async def _crawl_catalog(self, client: RetryableHTTPClient):
        """
        Crawl all catalog pages and extract book links.

        Args:
            client: HTTP client for making requests
        """
        current_url = self.base_url
        page_num = 1

        while current_url:
            log.info(f"Crawling catalog page {page_num}: {current_url}")

            # Fetch catalog page
            response = await client.get(current_url)
            if not response:
                log.error(f"Failed to fetch catalog page: {current_url}")
                self.stats["failed_pages"] += 1
                break

            # Extract book links
            book_urls = self.parser.extract_book_links(response.text, current_url)

            # Filter out already processed URLs
            new_book_urls = [
                url for url in book_urls
                if url not in self.stats["processed_urls"]
            ]

            log.info(f"Found {len(new_book_urls)} new books on page {page_num}")

            # Crawl books concurrently
            if new_book_urls:
                await self._crawl_books_batch(client, new_book_urls)

            # Get next page URL
            next_url = self.parser.get_next_page_url(response.text, current_url)

            if next_url:
                current_url = next_url
                page_num += 1
            else:
                log.info("No more catalog pages found")
                break

    async def _crawl_books_batch(
        self,
        client: RetryableHTTPClient,
        book_urls: List[str]
    ):
        """
        Crawl a batch of book detail pages concurrently.

        Args:
            client: HTTP client
            book_urls: List of book URLs to crawl
        """
        tasks = []
        for url in book_urls:
            task = self._crawl_book(client, url)
            tasks.append(task)

        # Process books concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

        # Save progress after each batch
        self._save_progress()

    async def _crawl_book(self, client: RetryableHTTPClient, book_url: str):
        """
        Crawl a single book detail page.

        Args:
            client: HTTP client
            book_url: URL of the book page
        """
        try:
            # Fetch book page
            response = await client.get(book_url)
            if not response:
                log.error(f"Failed to fetch book page: {book_url}")
                self.stats["failed_pages"] += 1
                return

            # Parse book details
            book_data = self.parser.parse_book_details(
                response.text,
                book_url,
                self.base_url
            )

            if not book_data:
                log.error(f"Failed to parse book data: {book_url}")
                self.stats["failed_pages"] += 1
                return

            # Validate with Pydantic schema
            try:
                book_create = BookCreate(**book_data)
            except Exception as e:
                log.error(f"Validation failed for {book_url}: {e}")
                self.stats["failed_pages"] += 1
                return

            # Check if book already exists
            existing_book = await db.get_book_by_url(book_url)

            if existing_book:
                # Update if content changed
                if existing_book.get("content_hash") != book_create.content_hash:
                    await db.update_book(book_url, book_create)
                    self.stats["updated_books"] += 1
                    log.info(f"Updated book: {book_create.name}")
                else:
                    log.debug(f"Book unchanged: {book_create.name}")
            else:
                # Insert new book
                await db.insert_book(book_create)
                self.stats["new_books"] += 1
                log.info(f"Inserted new book: {book_create.name}")

            # Mark as processed
            self.stats["processed_urls"].add(book_url)
            self.stats["total_books"] += 1

        except Exception as e:
            log.error(f"Error crawling book {book_url}: {e}")
            self.stats["failed_pages"] += 1

    def _save_progress(self):
        """Save crawl progress to file for resume capability."""
        try:
            progress_data = {
                "stats": {
                    "total_books": self.stats["total_books"],
                    "new_books": self.stats["new_books"],
                    "updated_books": self.stats["updated_books"],
                    "failed_pages": self.stats["failed_pages"],
                },
                "processed_urls": list(self.stats["processed_urls"]),
                "timestamp": datetime.utcnow().isoformat(),
            }

            with open(self.progress_file, "w") as f:
                json.dump(progress_data, f, indent=2)

            log.debug(f"Progress saved to {self.progress_file}")

        except Exception as e:
            log.error(f"Failed to save progress: {e}")

    def _load_progress(self):
        """Load crawl progress from file to resume."""
        try:
            if not self.progress_file.exists():
                log.info("No progress file found, starting fresh")
                return

            with open(self.progress_file, "r") as f:
                progress_data = json.load(f)

            self.stats["total_books"] = progress_data["stats"]["total_books"]
            self.stats["new_books"] = progress_data["stats"]["new_books"]
            self.stats["updated_books"] = progress_data["stats"]["updated_books"]
            self.stats["failed_pages"] = progress_data["stats"]["failed_pages"]
            self.stats["processed_urls"] = set(progress_data["processed_urls"])

            log.info(
                f"Resumed from checkpoint: {len(self.stats['processed_urls'])} "
                f"URLs already processed"
            )

        except Exception as e:
            log.error(f"Failed to load progress: {e}")
            log.info("Starting fresh")


async def run_scraper(resume: bool = True) -> Dict[str, Any]:
    """
    Run the book scraper.

    Args:
        resume: Whether to resume from last checkpoint

    Returns:
        Crawl statistics
    """
    scraper = BookScraper()
    return await scraper.crawl(resume=resume)
