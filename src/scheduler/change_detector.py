"""Change detection logic for monitoring book updates."""
import csv
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
from src.database.mongodb import db
from src.schemas.book import ChangeLog, ChangeType
from src.utils.logger import log
from src.utils.config import settings


class ChangeDetector:
    """Detect and log changes in book data."""

    def __init__(self):
        """Initialize change detector."""
        self.changes = []

    async def detect_changes(
        self,
        old_book: Dict[str, Any],
        new_book: Dict[str, Any]
    ) -> List[ChangeLog]:
        """
        Detect changes between old and new book data.

        Args:
            old_book: Previous book data from database
            new_book: New book data from crawl

        Returns:
            List of ChangeLog objects
        """
        changes = []
        book_id = str(old_book.get("_id", ""))
        book_name = new_book.get("name", old_book.get("name", "Unknown"))

        # Check for price changes
        old_price = old_book.get("price_incl_tax")
        new_price = new_book.get("price_incl_tax")
        if old_price != new_price:
            change = ChangeLog(
                book_id=book_id,
                book_name=book_name,
                change_type=ChangeType.PRICE_CHANGE,
                old_value=str(old_price),
                new_value=str(new_price),
                details={
                    "old_price_excl_tax": old_book.get("price_excl_tax"),
                    "new_price_excl_tax": new_book.get("price_excl_tax"),
                }
            )
            changes.append(change)
            log.info(
                f"Price change detected for '{book_name}': "
                f"${old_price} → ${new_price}"
            )

        # Check for availability changes
        old_availability = old_book.get("availability")
        new_availability = new_book.get("availability")
        if old_availability != new_availability:
            change = ChangeLog(
                book_id=book_id,
                book_name=book_name,
                change_type=ChangeType.AVAILABILITY_CHANGE,
                old_value=old_availability,
                new_value=new_availability,
            )
            changes.append(change)
            log.info(
                f"Availability change detected for '{book_name}': "
                f"{old_availability} → {new_availability}"
            )

        # Check for rating changes
        old_rating = old_book.get("rating")
        new_rating = new_book.get("rating")
        if old_rating != new_rating:
            change = ChangeLog(
                book_id=book_id,
                book_name=book_name,
                change_type=ChangeType.RATING_CHANGE,
                old_value=old_rating,
                new_value=new_rating,
            )
            changes.append(change)
            log.info(
                f"Rating change detected for '{book_name}': "
                f"{old_rating} → {new_rating}"
            )

        # Check for review count changes
        old_reviews = old_book.get("num_reviews")
        new_reviews = new_book.get("num_reviews")
        if old_reviews != new_reviews:
            change = ChangeLog(
                book_id=book_id,
                book_name=book_name,
                change_type=ChangeType.REVIEW_COUNT_CHANGE,
                old_value=str(old_reviews),
                new_value=str(new_reviews),
            )
            changes.append(change)
            log.info(
                f"Review count change detected for '{book_name}': "
                f"{old_reviews} → {new_reviews}"
            )

        # Check for description changes
        old_desc = old_book.get("description")
        new_desc = new_book.get("description")
        if old_desc != new_desc:
            change = ChangeLog(
                book_id=book_id,
                book_name=book_name,
                change_type=ChangeType.DESCRIPTION_CHANGE,
                old_value=old_desc[:100] if old_desc else None,
                new_value=new_desc[:100] if new_desc else None,
            )
            changes.append(change)
            log.info(f"Description change detected for '{book_name}'")

        # Log changes to database
        for change in changes:
            await db.insert_change_log(change)
            self.changes.append(change)

        return changes

    async def log_new_book(self, book_id: str, book_name: str):
        """
        Log a new book addition.

        Args:
            book_id: ID of the new book
            book_name: Name of the new book
        """
        change = ChangeLog(
            book_id=book_id,
            book_name=book_name,
            change_type=ChangeType.NEW_BOOK,
            new_value="Book added to database",
        )

        await db.insert_change_log(change)
        self.changes.append(change)
        log.info(f"New book detected: '{book_name}'")

    async def get_recent_changes(
        self,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent changes from the database.

        Args:
            hours: Number of hours to look back

        Returns:
            List of change log entries
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        # In a real implementation, this would query the database with a date filter
        # For now, we'll get all recent changes
        changes = await db.get_change_logs(limit=100)

        # Filter by time
        recent_changes = [
            change for change in changes
            if change.get("detected_at") and
            datetime.fromisoformat(change["detected_at"].replace("Z", "+00:00")) >= since
        ]

        return recent_changes

    def generate_change_report(
        self,
        output_format: str = "json",
        output_file: str = None
    ) -> str:
        """
        Generate a change report.

        Args:
            output_format: Format of the report (json or csv)
            output_file: Optional output file path

        Returns:
            Report content as string
        """
        if not self.changes:
            log.info("No changes to report")
            return ""

        # Create reports directory
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        # Generate filename if not provided
        if not output_file:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = reports_dir / f"change_report_{timestamp}.{output_format}"
        else:
            output_file = Path(output_file)

        if output_format == "json":
            report_data = {
                "generated_at": datetime.utcnow().isoformat(),
                "total_changes": len(self.changes),
                "changes": [
                    {
                        "book_id": change.book_id,
                        "book_name": change.book_name,
                        "change_type": change.change_type.value,
                        "old_value": change.old_value,
                        "new_value": change.new_value,
                        "detected_at": change.detected_at.isoformat(),
                        "details": change.details,
                    }
                    for change in self.changes
                ]
            }

            with open(output_file, "w") as f:
                json.dump(report_data, f, indent=2)

            log.info(f"JSON change report generated: {output_file}")
            return json.dumps(report_data, indent=2)

        elif output_format == "csv":
            with open(output_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Book ID", "Book Name", "Change Type",
                    "Old Value", "New Value", "Detected At"
                ])

                for change in self.changes:
                    writer.writerow([
                        change.book_id,
                        change.book_name,
                        change.change_type.value,
                        change.old_value or "",
                        change.new_value or "",
                        change.detected_at.isoformat(),
                    ])

            log.info(f"CSV change report generated: {output_file}")
            return str(output_file)

        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    async def send_alert_email(self, changes: List[ChangeLog]):
        """
        Send email alert for significant changes.

        Args:
            changes: List of changes to report
        """
        if not settings.email_alerts_enabled:
            log.info("Email alerts not configured, skipping")
            return

        if not changes:
            return

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Create email content
            subject = f"Book Scraper Alert: {len(changes)} changes detected"

            html_content = "<html><body>"
            html_content += f"<h2>Changes Detected: {len(changes)}</h2>"
            html_content += "<table border='1' cellpadding='5' cellspacing='0'>"
            html_content += "<tr><th>Book</th><th>Change Type</th><th>Old Value</th><th>New Value</th></tr>"

            for change in changes:
                html_content += f"<tr>"
                html_content += f"<td>{change.book_name}</td>"
                html_content += f"<td>{change.change_type.value}</td>"
                html_content += f"<td>{change.old_value or '-'}</td>"
                html_content += f"<td>{change.new_value or '-'}</td>"
                html_content += f"</tr>"

            html_content += "</table></body></html>"

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.smtp_user
            msg["To"] = settings.alert_email

            msg.attach(MIMEText(html_content, "html"))

            # Send email
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)

            log.info(f"Alert email sent to {settings.alert_email}")

        except Exception as e:
            log.error(f"Failed to send alert email: {e}")
