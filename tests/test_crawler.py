"""Tests for web crawler functionality."""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.crawler.parser import BookParser
from src.crawler.scraper import BookScraper


class TestBookParser:
    """Test cases for BookParser."""

    def test_parse_price(self):
        """Test price parsing from various formats."""
        parser = BookParser()

        assert parser._parse_price("£51.77") == 51.77
        assert parser._parse_price("$25.99") == 25.99
        assert parser._parse_price("10.50") == 10.50
        assert parser._parse_price("invalid") == 0.0

    def test_extract_book_links(self):
        """Test extracting book links from catalog page."""
        html = """
        <html>
            <article class="product_pod">
                <h3><a href="catalogue/book-1.html">Book 1</a></h3>
            </article>
            <article class="product_pod">
                <h3><a href="catalogue/book-2.html">Book 2</a></h3>
            </article>
        </html>
        """
        base_url = "http://example.com"

        parser = BookParser()
        links = parser.extract_book_links(html, base_url)

        assert len(links) == 2
        assert "http://example.com/catalogue/book-1.html" in links
        assert "http://example.com/catalogue/book-2.html" in links

    def test_get_next_page_url(self):
        """Test extracting next page URL."""
        html_with_next = """
        <html>
            <li class="next"><a href="catalogue/page-2.html">next</a></li>
        </html>
        """
        html_without_next = """
        <html>
            <li class="previous"><a href="catalogue/page-1.html">previous</a></li>
        </html>
        """

        parser = BookParser()
        current_url = "http://example.com/catalogue/page-1.html"

        next_url = parser.get_next_page_url(html_with_next, current_url)
        assert next_url is not None
        assert "page-2.html" in next_url

        next_url = parser.get_next_page_url(html_without_next, current_url)
        assert next_url is None

    def test_parse_book_details(self):
        """Test parsing book details from HTML."""
        html = """
        <html>
            <h1>Test Book</h1>
            <div id="product_description"></div>
            <p>This is a test book description.</p>
            <ul class="breadcrumb">
                <li><a href="/">Home</a></li>
                <li><a href="/books">Books</a></li>
                <li><a href="/fiction">Fiction</a></li>
            </ul>
            <table class="table table-striped">
                <tr><th>Price (excl. tax)</th><td>£50.00</td></tr>
                <tr><th>Price (incl. tax)</th><td>£50.00</td></tr>
                <tr><th>Number of reviews</th><td>5</td></tr>
            </table>
            <p class="instock availability">In stock (10 available)</p>
            <div class="item active"><img src="cover.jpg" /></div>
            <p class="star-rating Four"></p>
        </html>
        """

        parser = BookParser()
        book_data = parser.parse_book_details(
            html,
            "http://example.com/book.html",
            "http://example.com"
        )

        assert book_data is not None
        assert book_data["name"] == "Test Book"
        assert book_data["category"] == "Fiction"
        assert book_data["price_incl_tax"] == 50.0
        assert book_data["num_reviews"] == 5
        assert book_data["rating"] == "Four"
        assert "content_hash" in book_data


@pytest.mark.asyncio
class TestBookScraper:
    """Test cases for BookScraper."""

    async def test_scraper_initialization(self):
        """Test scraper initialization."""
        scraper = BookScraper(base_url="http://example.com")

        assert scraper.base_url == "http://example.com"
        assert scraper.parser is not None
        assert scraper.stats["total_books"] == 0

    @patch('src.crawler.scraper.db')
    async def test_save_progress(self, mock_db):
        """Test saving crawl progress."""
        scraper = BookScraper()
        scraper.stats["total_books"] = 10
        scraper.stats["processed_urls"] = {"http://example.com/book1"}

        scraper._save_progress()

        assert scraper.progress_file.exists()

        # Clean up
        if scraper.progress_file.exists():
            scraper.progress_file.unlink()

    @patch('src.crawler.scraper.db')
    async def test_load_progress(self, mock_db):
        """Test loading crawl progress."""
        scraper = BookScraper()

        # Create a progress file
        scraper.stats["total_books"] = 15
        scraper.stats["processed_urls"] = {"http://example.com/book1", "http://example.com/book2"}
        scraper._save_progress()

        # Create new scraper and load progress
        new_scraper = BookScraper()
        new_scraper._load_progress()

        assert new_scraper.stats["total_books"] == 15
        assert len(new_scraper.stats["processed_urls"]) == 2

        # Clean up
        if scraper.progress_file.exists():
            scraper.progress_file.unlink()
