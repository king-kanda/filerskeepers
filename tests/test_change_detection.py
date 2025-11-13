"""Tests for change detection functionality."""
import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock
from src.scheduler.change_detector import ChangeDetector
from src.schemas.book import ChangeType


@pytest.fixture
def old_book_data():
    """Old book data for testing."""
    return {
        "_id": "507f1f77bcf86cd799439011",
        "name": "Test Book",
        "description": "Old description",
        "category": "Fiction",
        "price_excl_tax": 45.0,
        "price_incl_tax": 50.0,
        "availability": "In stock",
        "num_reviews": 10,
        "image_url": "http://example.com/image.jpg",
        "rating": "Four",
        "source_url": "http://example.com/book.html",
    }


@pytest.fixture
def new_book_data():
    """New book data with changes."""
    return {
        "name": "Test Book",
        "description": "New description",
        "category": "Fiction",
        "price_excl_tax": 40.0,
        "price_incl_tax": 45.0,
        "availability": "In stock",
        "num_reviews": 15,
        "image_url": "http://example.com/image.jpg",
        "rating": "Five",
        "source_url": "http://example.com/book.html",
    }


@pytest.mark.asyncio
class TestChangeDetector:
    """Test cases for ChangeDetector."""

    async def test_initialization(self):
        """Test change detector initialization."""
        detector = ChangeDetector()
        assert detector.changes == []

    @patch('src.scheduler.change_detector.db')
    async def test_detect_price_change(self, mock_db, old_book_data, new_book_data):
        """Test detecting price changes."""
        mock_db.insert_change_log = AsyncMock()

        detector = ChangeDetector()
        changes = await detector.detect_changes(old_book_data, new_book_data)

        # Should detect price change
        price_changes = [c for c in changes if c.change_type == ChangeType.PRICE_CHANGE]
        assert len(price_changes) == 1
        assert price_changes[0].old_value == "50.0"
        assert price_changes[0].new_value == "45.0"

    @patch('src.scheduler.change_detector.db')
    async def test_detect_rating_change(self, mock_db, old_book_data, new_book_data):
        """Test detecting rating changes."""
        mock_db.insert_change_log = AsyncMock()

        detector = ChangeDetector()
        changes = await detector.detect_changes(old_book_data, new_book_data)

        # Should detect rating change
        rating_changes = [c for c in changes if c.change_type == ChangeType.RATING_CHANGE]
        assert len(rating_changes) == 1
        assert rating_changes[0].old_value == "Four"
        assert rating_changes[0].new_value == "Five"

    @patch('src.scheduler.change_detector.db')
    async def test_detect_review_count_change(self, mock_db, old_book_data, new_book_data):
        """Test detecting review count changes."""
        mock_db.insert_change_log = AsyncMock()

        detector = ChangeDetector()
        changes = await detector.detect_changes(old_book_data, new_book_data)

        # Should detect review count change
        review_changes = [c for c in changes if c.change_type == ChangeType.REVIEW_COUNT_CHANGE]
        assert len(review_changes) == 1
        assert review_changes[0].old_value == "10"
        assert review_changes[0].new_value == "15"

    @patch('src.scheduler.change_detector.db')
    async def test_detect_description_change(self, mock_db, old_book_data, new_book_data):
        """Test detecting description changes."""
        mock_db.insert_change_log = AsyncMock()

        detector = ChangeDetector()
        changes = await detector.detect_changes(old_book_data, new_book_data)

        # Should detect description change
        desc_changes = [c for c in changes if c.change_type == ChangeType.DESCRIPTION_CHANGE]
        assert len(desc_changes) == 1

    @patch('src.scheduler.change_detector.db')
    async def test_detect_availability_change(self, mock_db, old_book_data):
        """Test detecting availability changes."""
        mock_db.insert_change_log = AsyncMock()

        new_data = old_book_data.copy()
        new_data["availability"] = "Out of stock"

        detector = ChangeDetector()
        changes = await detector.detect_changes(old_book_data, new_data)

        # Should detect availability change
        avail_changes = [c for c in changes if c.change_type == ChangeType.AVAILABILITY_CHANGE]
        assert len(avail_changes) == 1
        assert avail_changes[0].old_value == "In stock"
        assert avail_changes[0].new_value == "Out of stock"

    @patch('src.scheduler.change_detector.db')
    async def test_log_new_book(self, mock_db):
        """Test logging new book addition."""
        mock_db.insert_change_log = AsyncMock()

        detector = ChangeDetector()
        await detector.log_new_book("507f1f77bcf86cd799439011", "New Test Book")

        assert len(detector.changes) == 1
        assert detector.changes[0].change_type == ChangeType.NEW_BOOK
        assert detector.changes[0].book_name == "New Test Book"

    def test_generate_json_report(self):
        """Test generating JSON change report."""
        detector = ChangeDetector()

        # Add mock changes
        from src.schemas.book import ChangeLog
        change = ChangeLog(
            book_id="507f1f77bcf86cd799439011",
            book_name="Test Book",
            change_type=ChangeType.PRICE_CHANGE,
            old_value="50.0",
            new_value="45.0"
        )
        detector.changes.append(change)

        report = detector.generate_change_report(
            output_format="json",
            output_file="test_report.json"
        )

        assert "Test Book" in report
        assert "price_change" in report

        # Clean up
        import os
        if os.path.exists("test_report.json"):
            os.remove("test_report.json")

    def test_generate_csv_report(self):
        """Test generating CSV change report."""
        detector = ChangeDetector()

        # Add mock changes
        from src.schemas.book import ChangeLog
        change = ChangeLog(
            book_id="507f1f77bcf86cd799439011",
            book_name="Test Book",
            change_type=ChangeType.PRICE_CHANGE,
            old_value="50.0",
            new_value="45.0"
        )
        detector.changes.append(change)

        report_file = detector.generate_change_report(
            output_format="csv",
            output_file="test_report.csv"
        )

        import os
        assert os.path.exists("test_report.csv")

        # Clean up
        if os.path.exists("test_report.csv"):
            os.remove("test_report.csv")
