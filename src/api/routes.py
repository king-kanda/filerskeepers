"""API route definitions."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from src.api.auth import verify_api_key
from src.api.rate_limiter import limiter
from src.database.mongodb import db
from src.schemas.book import (
    BookResponse,
    PaginatedResponse,
    ChangeLogResponse,
    BookQueryParams,
)
from src.utils.logger import log
from bson import ObjectId


# Create router
router = APIRouter(prefix="/api/v1", tags=["books"])


@router.get(
    "/books",
    response_model=PaginatedResponse,
    summary="Get books with filtering and pagination",
    description="Retrieve a paginated list of books with optional filtering by category, price range, and rating."
)
@limiter.limit(f"100/hour")
async def get_books(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price (inclusive)"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price (inclusive)"),
    rating: Optional[str] = Query(None, description="Filter by rating (One, Two, Three, Four, Five)"),
    sort_by: Optional[str] = Query(None, description="Sort by field: rating, price, reviews (prefix with - for descending)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    api_key: str = Depends(verify_api_key)
):
    """Get books with optional filtering, sorting, and pagination."""
    try:
        # Build query filters
        filters = {}

        if category:
            filters["category"] = category

        if min_price is not None or max_price is not None:
            price_filter = {}
            if min_price is not None:
                price_filter["$gte"] = min_price
            if max_price is not None:
                price_filter["$lte"] = max_price
            filters["price_incl_tax"] = price_filter

        if rating:
            valid_ratings = ["One", "Two", "Three", "Four", "Five"]
            if rating not in valid_ratings:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid rating. Must be one of: {', '.join(valid_ratings)}"
                )
            filters["rating"] = rating

        # Calculate pagination
        skip = (page - 1) * page_size

        # Get books from database
        books = await db.get_books(
            filters=filters,
            sort_by=sort_by,
            skip=skip,
            limit=page_size
        )

        # Get total count
        total = await db.count_books(filters=filters)

        # Convert to response models
        book_responses = []
        for book in books:
            book_response = BookResponse(
                id=book["_id"],
                name=book["name"],
                description=book.get("description"),
                category=book["category"],
                price_excl_tax=book["price_excl_tax"],
                price_incl_tax=book["price_incl_tax"],
                availability=book["availability"],
                num_reviews=book["num_reviews"],
                image_url=book["image_url"],
                rating=book["rating"],
                source_url=book["source_url"],
                crawl_timestamp=book["crawl_timestamp"],
                last_updated=book["last_updated"],
            )
            book_responses.append(book_response)

        # Create paginated response
        response = PaginatedResponse.create(
            items=book_responses,
            total=total,
            page=page,
            page_size=page_size
        )

        log.info(f"Returned {len(book_responses)} books (page {page}/{response.total_pages})")
        return response

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error fetching books: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch books"
        )


@router.get(
    "/books/{book_id}",
    response_model=BookResponse,
    summary="Get book by ID",
    description="Retrieve detailed information about a specific book by its ID."
)
@limiter.limit(f"100/hour")
async def get_book_by_id(
    request: Request,
    book_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get a specific book by ID."""
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(book_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid book ID format"
            )

        # Get book from database
        book = await db.get_book_by_id(book_id)

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with ID {book_id} not found"
            )

        # Convert to response model
        book_response = BookResponse(
            id=book["_id"],
            name=book["name"],
            description=book.get("description"),
            category=book["category"],
            price_excl_tax=book["price_excl_tax"],
            price_incl_tax=book["price_incl_tax"],
            availability=book["availability"],
            num_reviews=book["num_reviews"],
            image_url=book["image_url"],
            rating=book["rating"],
            source_url=book["source_url"],
            crawl_timestamp=book["crawl_timestamp"],
            last_updated=book["last_updated"],
        )

        log.info(f"Returned book: {book['name']} (ID: {book_id})")
        return book_response

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error fetching book {book_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch book"
        )


@router.get(
    "/changes",
    response_model=List[ChangeLogResponse],
    summary="Get recent changes",
    description="Retrieve recent updates and changes to books, such as price changes, new books, availability changes, etc."
)
@limiter.limit(f"100/hour")
async def get_changes(
    request: Request,
    book_id: Optional[str] = Query(None, description="Filter by book ID"),
    change_type: Optional[str] = Query(None, description="Filter by change type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    api_key: str = Depends(verify_api_key)
):
    """Get recent changes with optional filtering."""
    try:
        # Validate book_id if provided
        if book_id and not ObjectId.is_valid(book_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid book ID format"
            )

        # Validate change_type if provided
        if change_type:
            valid_types = [
                "new_book", "price_change", "availability_change",
                "description_change", "rating_change", "review_count_change",
                "other_change"
            ]
            if change_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid change_type. Must be one of: {', '.join(valid_types)}"
                )

        # Calculate pagination
        skip = (page - 1) * page_size

        # Get changes from database
        changes = await db.get_change_logs(
            skip=skip,
            limit=page_size,
            book_id=book_id,
            change_type=change_type
        )

        # Convert to response models
        change_responses = []
        for change in changes:
            change_response = ChangeLogResponse(
                id=change["_id"],
                book_id=change["book_id"],
                book_name=change["book_name"],
                change_type=change["change_type"],
                old_value=change.get("old_value"),
                new_value=change.get("new_value"),
                detected_at=change["detected_at"],
                details=change.get("details"),
            )
            change_responses.append(change_response)

        log.info(f"Returned {len(change_responses)} change logs (page {page})")
        return change_responses

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error fetching changes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch changes"
        )


