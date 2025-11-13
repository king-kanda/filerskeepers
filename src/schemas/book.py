"""Pydantic schemas for book data validation and serialization."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, field_validator
from enum import Enum


class RatingEnum(str, Enum):
    """Book rating enumeration."""
    ONE = "One"
    TWO = "Two"
    THREE = "Three"
    FOUR = "Four"
    FIVE = "Five"


class AvailabilityEnum(str, Enum):
    """Book availability status."""
    IN_STOCK = "In stock"
    OUT_OF_STOCK = "Out of stock"


class BookBase(BaseModel):
    """Base book schema with core fields."""
    name: str = Field(..., description="Name of the book", min_length=1)
    description: Optional[str] = Field(None, description="Book description")
    category: str = Field(..., description="Book category")
    price_excl_tax: float = Field(..., description="Price excluding tax", ge=0)
    price_incl_tax: float = Field(..., description="Price including tax", ge=0)
    availability: str = Field(..., description="Availability status")
    num_reviews: int = Field(..., description="Number of reviews", ge=0)
    image_url: str = Field(..., description="Book cover image URL")
    rating: str = Field(..., description="Book rating (One to Five)")
    source_url: str = Field(..., description="Source URL of the book page")

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v: str) -> str:
        """Validate rating is one of the valid values."""
        valid_ratings = ["One", "Two", "Three", "Four", "Five"]
        if v not in valid_ratings:
            raise ValueError(f"Rating must be one of: {', '.join(valid_ratings)}")
        return v

    @field_validator('price_excl_tax', 'price_incl_tax')
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Validate and round price to 2 decimal places."""
        return round(v, 2)


class BookCreate(BookBase):
    """Schema for creating a new book."""
    raw_html: str = Field(..., description="Raw HTML snapshot of the book page")
    content_hash: str = Field(..., description="Hash of book content for change detection")


class BookInDB(BookBase):
    """Schema for book stored in database."""
    id: str = Field(..., alias="_id", description="MongoDB document ID")
    raw_html: str = Field(..., description="Raw HTML snapshot")
    content_hash: str = Field(..., description="Content hash for change detection")
    crawl_timestamp: datetime = Field(..., description="When this data was crawled")
    last_updated: datetime = Field(..., description="Last update timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BookResponse(BookBase):
    """Schema for API responses."""
    id: str = Field(..., description="Book ID")
    crawl_timestamp: datetime = Field(..., description="When this data was crawled")
    last_updated: datetime = Field(..., description="Last update timestamp")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChangeType(str, Enum):
    """Type of change detected."""
    NEW_BOOK = "new_book"
    PRICE_CHANGE = "price_change"
    AVAILABILITY_CHANGE = "availability_change"
    DESCRIPTION_CHANGE = "description_change"
    RATING_CHANGE = "rating_change"
    REVIEW_COUNT_CHANGE = "review_count_change"
    OTHER_CHANGE = "other_change"


class ChangeLog(BaseModel):
    """Schema for tracking changes to books."""
    book_id: str = Field(..., description="ID of the book that changed")
    book_name: str = Field(..., description="Name of the book")
    change_type: ChangeType = Field(..., description="Type of change")
    old_value: Optional[str] = Field(None, description="Previous value")
    new_value: Optional[str] = Field(None, description="New value")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="When the change was detected")
    details: Optional[dict] = Field(default=None, description="Additional change details")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChangeLogResponse(ChangeLog):
    """Schema for change log API responses."""
    id: str = Field(..., description="Change log entry ID")

    class Config:
        populate_by_name = True


class CrawlStatus(BaseModel):
    """Schema for crawler status and statistics."""
    total_books: int = Field(..., description="Total number of books crawled")
    new_books: int = Field(default=0, description="Number of new books added")
    updated_books: int = Field(default=0, description="Number of books updated")
    failed_pages: int = Field(default=0, description="Number of failed pages")
    crawl_started: datetime = Field(..., description="Crawl start time")
    crawl_finished: Optional[datetime] = Field(None, description="Crawl finish time")
    status: str = Field(..., description="Crawl status (running, completed, failed)")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginatedResponse(BaseModel):
    """Generic paginated response schema."""
    items: List[BookResponse] = Field(..., description="List of books")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")

    @classmethod
    def create(cls, items: List[BookResponse], total: int, page: int, page_size: int):
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


class BookQueryParams(BaseModel):
    """Query parameters for filtering books."""
    category: Optional[str] = Field(None, description="Filter by category")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price (inclusive)")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price (inclusive)")
    rating: Optional[str] = Field(None, description="Filter by rating")
    sort_by: Optional[str] = Field(None, description="Sort field (rating, price, reviews)")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @field_validator('sort_by')
    @classmethod
    def validate_sort_by(cls, v: Optional[str]) -> Optional[str]:
        """Validate sort_by field."""
        if v is not None:
            valid_sorts = ["rating", "price", "reviews", "-rating", "-price", "-reviews"]
            if v not in valid_sorts:
                raise ValueError(f"sort_by must be one of: {', '.join(valid_sorts)}")
        return v
