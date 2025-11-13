"""MongoDB database connection and operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
from src.utils.config import settings
from src.utils.logger import log
from src.schemas.book import BookCreate, BookInDB, ChangeLog


class MongoDB:
    """MongoDB database manager with async operations."""

    def __init__(self):
        """Initialize MongoDB connection."""
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        """Connect to MongoDB and create indexes."""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.db = self.client[settings.mongodb_db_name]
            await self._create_indexes()
            log.info(f"Connected to MongoDB: {settings.mongodb_db_name}")
        except Exception as e:
            log.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            log.info("Disconnected from MongoDB")

    async def _create_indexes(self):
        """Create indexes for efficient querying."""
        # Books collection indexes
        books_collection = self.db.books
        await books_collection.create_index("source_url", unique=True)
        await books_collection.create_index("content_hash")
        await books_collection.create_index("category")
        await books_collection.create_index("price_incl_tax")
        await books_collection.create_index("rating")
        await books_collection.create_index("num_reviews")
        await books_collection.create_index("crawl_timestamp")
        await books_collection.create_index([
            ("category", ASCENDING),
            ("price_incl_tax", ASCENDING),
        ])

        # Change logs collection indexes
        changelog_collection = self.db.change_logs
        await changelog_collection.create_index("book_id")
        await changelog_collection.create_index("change_type")
        await changelog_collection.create_index("detected_at")
        await changelog_collection.create_index([
            ("detected_at", DESCENDING)
        ])

        # Crawl status collection indexes
        crawl_status_collection = self.db.crawl_status
        await crawl_status_collection.create_index("crawl_started")

        log.info("Database indexes created successfully")

    async def insert_book(self, book_data: BookCreate) -> str:
        """Insert a new book into the database."""
        try:
            book_dict = book_data.model_dump()
            book_dict["crawl_timestamp"] = datetime.utcnow()
            book_dict["last_updated"] = datetime.utcnow()
            book_dict["created_at"] = datetime.utcnow()

            result = await self.db.books.insert_one(book_dict)
            log.info(f"Inserted new book: {book_data.name} (ID: {result.inserted_id})")
            return str(result.inserted_id)
        except DuplicateKeyError:
            log.warning(f"Book already exists: {book_data.source_url}")
            raise ValueError(f"Book with URL {book_data.source_url} already exists")
        except Exception as e:
            log.error(f"Failed to insert book: {e}")
            raise

    async def update_book(
        self,
        source_url: str,
        book_data: BookCreate
    ) -> bool:
        """Update an existing book in the database."""
        try:
            book_dict = book_data.model_dump()
            book_dict["last_updated"] = datetime.utcnow()
            book_dict["crawl_timestamp"] = datetime.utcnow()

            result = await self.db.books.update_one(
                {"source_url": source_url},
                {"$set": book_dict}
            )

            if result.modified_count > 0:
                log.info(f"Updated book: {book_data.name}")
                return True
            return False
        except Exception as e:
            log.error(f"Failed to update book: {e}")
            raise

    async def get_book_by_url(self, source_url: str) -> Optional[Dict[str, Any]]:
        """Get a book by its source URL."""
        try:
            book = await self.db.books.find_one({"source_url": source_url})
            if book:
                book["_id"] = str(book["_id"])
            return book
        except Exception as e:
            log.error(f"Failed to get book by URL: {e}")
            raise

    async def get_book_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Get a book by its ID."""
        try:
            from bson import ObjectId
            book = await self.db.books.find_one({"_id": ObjectId(book_id)})
            if book:
                book["_id"] = str(book["_id"])
            return book
        except Exception as e:
            log.error(f"Failed to get book by ID: {e}")
            return None

    async def get_books(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get books with optional filtering, sorting, and pagination."""
        try:
            query = filters or {}

            # Build sort criteria
            sort_criteria = []
            if sort_by:
                direction = DESCENDING if sort_by.startswith("-") else ASCENDING
                field = sort_by.lstrip("-")

                # Map sort fields
                field_mapping = {
                    "price": "price_incl_tax",
                    "reviews": "num_reviews",
                    "rating": "rating"
                }
                sort_field = field_mapping.get(field, field)
                sort_criteria.append((sort_field, direction))

            cursor = self.db.books.find(query)

            if sort_criteria:
                cursor = cursor.sort(sort_criteria)

            cursor = cursor.skip(skip).limit(limit)

            books = await cursor.to_list(length=limit)

            # Convert ObjectId to string
            for book in books:
                book["_id"] = str(book["_id"])

            return books
        except Exception as e:
            log.error(f"Failed to get books: {e}")
            raise

    async def count_books(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count books matching filters."""
        try:
            query = filters or {}
            count = await self.db.books.count_documents(query)
            return count
        except Exception as e:
            log.error(f"Failed to count books: {e}")
            raise

    async def insert_change_log(self, change_log: ChangeLog) -> str:
        """Insert a change log entry."""
        try:
            log_dict = change_log.model_dump()
            result = await self.db.change_logs.insert_one(log_dict)
            log.info(f"Logged change: {change_log.change_type} for book {change_log.book_name}")
            return str(result.inserted_id)
        except Exception as e:
            log.error(f"Failed to insert change log: {e}")
            raise

    async def get_change_logs(
        self,
        skip: int = 0,
        limit: int = 50,
        book_id: Optional[str] = None,
        change_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get change logs with optional filtering and pagination."""
        try:
            query = {}
            if book_id:
                query["book_id"] = book_id
            if change_type:
                query["change_type"] = change_type

            cursor = self.db.change_logs.find(query).sort("detected_at", DESCENDING)
            cursor = cursor.skip(skip).limit(limit)

            logs = await cursor.to_list(length=limit)

            # Convert ObjectId to string
            for log_entry in logs:
                log_entry["_id"] = str(log_entry["_id"])

            return logs
        except Exception as e:
            log.error(f"Failed to get change logs: {e}")
            raise

    async def count_change_logs(
        self,
        book_id: Optional[str] = None,
        change_type: Optional[str] = None
    ) -> int:
        """Count change logs matching filters."""
        try:
            query = {}
            if book_id:
                query["book_id"] = book_id
            if change_type:
                query["change_type"] = change_type

            count = await self.db.change_logs.count_documents(query)
            return count
        except Exception as e:
            log.error(f"Failed to count change logs: {e}")
            raise

    async def save_crawl_status(self, status_data: Dict[str, Any]) -> str:
        """Save crawl status to database."""
        try:
            result = await self.db.crawl_status.insert_one(status_data)
            return str(result.inserted_id)
        except Exception as e:
            log.error(f"Failed to save crawl status: {e}")
            raise

    async def get_last_crawl_status(self) -> Optional[Dict[str, Any]]:
        """Get the most recent crawl status."""
        try:
            status = await self.db.crawl_status.find_one(
                sort=[("crawl_started", DESCENDING)]
            )
            if status:
                status["_id"] = str(status["_id"])
            return status
        except Exception as e:
            log.error(f"Failed to get last crawl status: {e}")
            return None


# Global database instance
db = MongoDB()
