"""HTML parsing utilities for extracting book data."""
import re
import hashlib
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from src.utils.logger import log


class BookParser:
    """Parser for extracting book information from HTML."""

    @staticmethod
    def parse_book_details(html: str, book_url: str, base_url: str) -> Optional[Dict[str, Any]]:
        """
        Parse book details from HTML page.

        Args:
            html: Raw HTML content
            book_url: URL of the book page
            base_url: Base URL for resolving relative URLs

        Returns:
            Dictionary with book data or None if parsing fails
        """
        try:
            soup = BeautifulSoup(html, "lxml")

            # Extract book name
            name = soup.find("h1")
            if not name:
                log.warning(f"Failed to find book name in {book_url}")
                return None
            name = name.text.strip()

            # Extract description
            description_tag = soup.find("div", id="product_description")
            description = None
            if description_tag:
                desc_p = description_tag.find_next_sibling("p")
                if desc_p:
                    description = desc_p.text.strip()

            # Extract category (breadcrumb)
            breadcrumb = soup.find("ul", class_="breadcrumb")
            category = "Unknown"
            if breadcrumb:
                category_link = breadcrumb.find_all("a")
                if len(category_link) >= 3:
                    category = category_link[2].text.strip()

            # Extract price information
            product_info_table = soup.find("table", class_="table table-striped")
            price_excl_tax = 0.0
            price_incl_tax = 0.0

            if product_info_table:
                rows = product_info_table.find_all("tr")
                for row in rows:
                    header = row.find("th")
                    if header:
                        if "Price (excl. tax)" in header.text:
                            price_text = row.find("td").text.strip()
                            price_excl_tax = BookParser._parse_price(price_text)
                        elif "Price (incl. tax)" in header.text:
                            price_text = row.find("td").text.strip()
                            price_incl_tax = BookParser._parse_price(price_text)

            # Extract availability
            availability_tag = soup.find("p", class_="instock availability")
            availability = "Unknown"
            if availability_tag:
                availability = availability_tag.text.strip()
                # Clean up the availability text
                availability = re.sub(r'\s+', ' ', availability).strip()

            # Extract number of reviews
            num_reviews = 0
            if product_info_table:
                rows = product_info_table.find_all("tr")
                for row in rows:
                    header = row.find("th")
                    if header and "Number of reviews" in header.text:
                        num_reviews_text = row.find("td").text.strip()
                        num_reviews = int(num_reviews_text)

            # Extract image URL
            image_tag = soup.find("div", class_="item active")
            image_url = ""
            if image_tag:
                img = image_tag.find("img")
                if img and img.get("src"):
                    # Resolve relative URL
                    image_url = urljoin(base_url, img["src"])

            # Extract rating
            rating_tag = soup.find("p", class_=re.compile(r"star-rating"))
            rating = "Unknown"
            if rating_tag:
                rating_class = rating_tag.get("class", [])
                for cls in rating_class:
                    if cls in ["One", "Two", "Three", "Four", "Five"]:
                        rating = cls
                        break

            # Create content hash for change detection
            content_for_hash = f"{name}|{price_incl_tax}|{availability}|{num_reviews}|{rating}"
            content_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()

            book_data = {
                "name": name,
                "description": description,
                "category": category,
                "price_excl_tax": price_excl_tax,
                "price_incl_tax": price_incl_tax,
                "availability": availability,
                "num_reviews": num_reviews,
                "image_url": image_url,
                "rating": rating,
                "source_url": book_url,
                "raw_html": html,
                "content_hash": content_hash,
            }

            return book_data

        except Exception as e:
            log.error(f"Error parsing book details from {book_url}: {e}")
            return None

    @staticmethod
    def _parse_price(price_text: str) -> float:
        """Extract numeric price from text like '£51.77'."""
        try:
            # Remove currency symbols and parse float
            price_str = re.sub(r'[^\d.]', '', price_text)
            return float(price_str)
        except (ValueError, AttributeError):
            return 0.0

    @staticmethod
    def extract_book_links(html: str, base_url: str) -> list:
        """
        Extract book detail page links from a catalog page.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative URLs

        Returns:
            List of absolute URLs to book detail pages
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            book_links = []

            # Find all book containers
            articles = soup.find_all("article", class_="product_pod")

            for article in articles:
                h3_tag = article.find("h3")
                if h3_tag:
                    a_tag = h3_tag.find("a")
                    if a_tag and a_tag.get("href"):
                        # Resolve relative URL
                        book_url = urljoin(base_url, a_tag["href"])
                        book_links.append(book_url)

            log.info(f"Extracted {len(book_links)} book links from page")
            return book_links

        except Exception as e:
            log.error(f"Error extracting book links: {e}")
            return []

    @staticmethod
    def get_next_page_url(html: str, current_url: str) -> Optional[str]:
        """
        Extract the next page URL from pagination.

        Args:
            html: Raw HTML content
            current_url: Current page URL

        Returns:
            Absolute URL to next page or None if no next page
        """
        try:
            soup = BeautifulSoup(html, "lxml")

            # Find pagination
            next_button = soup.find("li", class_="next")
            if next_button:
                a_tag = next_button.find("a")
                if a_tag and a_tag.get("href"):
                    # Resolve relative URL
                    next_url = urljoin(current_url, a_tag["href"])
                    return next_url

            return None

        except Exception as e:
            log.error(f"Error extracting next page URL: {e}")
            return None
