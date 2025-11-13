"""Scheduler for periodic crawling and change detection."""
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.crawler.scraper import run_scraper
from src.scheduler.change_detector import ChangeDetector
from src.utils.config import settings
from src.utils.logger import log


class CrawlScheduler:
    """Scheduler for automated book crawling and change detection."""

    def __init__(self, event_loop=None):
        """Initialize the scheduler."""
        self.scheduler = AsyncIOScheduler(event_loop=event_loop)
        self.change_detector = ChangeDetector()
        self.is_running = False

    def start(self):
        """Start the scheduler."""
        if self.is_running:
            log.warning("Scheduler is already running")
            return

        # Schedule daily crawl
        self.scheduler.add_job(
            self.run_daily_crawl,
            trigger=CronTrigger(
                hour=settings.crawl_schedule_hour,
                minute=settings.crawl_schedule_minute
            ),
            id="daily_crawl",
            name="Daily Book Crawl",
            replace_existing=True,
        )

        # Schedule daily report generation (1 hour after crawl)
        report_hour = (settings.crawl_schedule_hour + 1) % 24
        self.scheduler.add_job(
            self.generate_daily_report,
            trigger=CronTrigger(
                hour=report_hour,
                minute=settings.crawl_schedule_minute
            ),
            id="daily_report",
            name="Daily Change Report",
            replace_existing=True,
        )

        self.scheduler.start()
        self.is_running = True

        log.info(
            f"Scheduler started. Daily crawl scheduled at "
            f"{settings.crawl_schedule_hour:02d}:{settings.crawl_schedule_minute:02d}"
        )

    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return

        self.scheduler.shutdown()
        self.is_running = False
        log.info("Scheduler stopped")

    async def run_daily_crawl(self):
        """Execute daily crawl with change detection."""
        log.info("Starting scheduled daily crawl")

        try:
            # Run the scraper
            stats = await run_scraper(resume=False)

            log.info(
                f"Daily crawl completed: {stats['total_books']} books processed, "
                f"{stats['new_books']} new, {stats['updated_books']} updated"
            )

            # Send alert if there are significant changes
            recent_changes = await self.change_detector.get_recent_changes(hours=1)

            if recent_changes:
                log.info(f"Detected {len(recent_changes)} changes in last hour")

                # Send email alert if configured
                from src.schemas.book import ChangeLog
                change_objects = [
                    ChangeLog(**change) for change in recent_changes
                ]
                await self.change_detector.send_alert_email(change_objects)

        except Exception as e:
            log.error(f"Daily crawl failed: {e}")

    async def generate_daily_report(self):
        """Generate daily change report."""
        log.info("Generating daily change report")

        try:
            # Get changes from last 24 hours
            changes = await self.change_detector.get_recent_changes(hours=24)

            if changes:
                # Reconstruct ChangeLog objects
                from src.schemas.book import ChangeLog, ChangeType
                change_objects = []

                for change in changes:
                    try:
                        change_obj = ChangeLog(
                            book_id=change["book_id"],
                            book_name=change["book_name"],
                            change_type=ChangeType(change["change_type"]),
                            old_value=change.get("old_value"),
                            new_value=change.get("new_value"),
                            detected_at=change["detected_at"],
                            details=change.get("details"),
                        )
                        change_objects.append(change_obj)
                    except Exception as e:
                        log.error(f"Failed to parse change log: {e}")

                # Set changes in detector
                self.change_detector.changes = change_objects

                # Generate reports in both formats
                self.change_detector.generate_change_report(output_format="json")
                self.change_detector.generate_change_report(output_format="csv")

                log.info(f"Generated daily report with {len(changes)} changes")
            else:
                log.info("No changes in the last 24 hours")

        except Exception as e:
            log.error(f"Failed to generate daily report: {e}")

    async def run_manual_crawl(self) -> dict:
        """
        Run a manual crawl immediately.

        Returns:
            Crawl statistics
        """
        log.info("Starting manual crawl")
        return await run_scraper(resume=True)


def run_scheduler():
    """Run the scheduler in blocking mode."""
    # Create event loop before creating AsyncIOScheduler
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Pass event loop explicitly to scheduler
    scheduler = CrawlScheduler(event_loop=loop)
    scheduler.start()

    log.info("Scheduler is running. Press Ctrl+C to exit.")

    try:
        # Keep the scheduler running
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        log.info("Shutting down scheduler...")
        scheduler.stop()


async def run_scheduler_async():
    """Run the scheduler asynchronously (for integration with API server)."""
    scheduler = CrawlScheduler()
    scheduler.start()

    try:
        # Keep running
        while scheduler.is_running:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.stop()
