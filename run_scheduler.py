"""Script to run the scheduler for automated crawling."""
import sys
from src.scheduler.scheduler import run_scheduler
from src.utils.logger import log


def main():
    """Main entry point for scheduler."""
    try:
        log.info("=" * 60)
        log.info("Starting Books Scraper Scheduler")
        log.info("=" * 60)

        # Run the scheduler (blocking)
        run_scheduler()

        return 0

    except KeyboardInterrupt:
        log.info("Scheduler interrupted by user")
        return 0
    except Exception as e:
        log.error(f"Scheduler failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
