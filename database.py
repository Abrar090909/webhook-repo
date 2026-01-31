"""
Database module for MongoDB operations.
Handles connection, event storage, and data retrieval.
"""

from pymongo import MongoClient, DESCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from datetime import datetime, timezone
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """MongoDB database handler for webhook events."""
    
    def __init__(self):
        """Initialize MongoDB connection (lazy)."""
        self.client = None
        self.db = None
        self.collection = None
        # We don't call connect() here to avoid blocking module import
    
    def connect(self):
        """
        Establish connection to MongoDB Atlas.
        """
        if self.collection:
            return

        try:
            # Reduced timeouts to fit within Vercel's 10s limit
            self.client = MongoClient(
                Config.MONGODB_URI,
                serverSelectionTimeoutMS=8000,
                connectTimeoutMS=8000,
                socketTimeoutMS=8000,
                connect=False
            )
            
            # Get database and collection
            self.db = self.client[Config.DATABASE_NAME]
            self.collection = self.db[Config.COLLECTION_NAME]
            
            # Try to initialize the collection (create index)
            # This will happen on the first request if lazy
            try:
                self.collection.create_index("request_id", unique=True)
                logger.info(f"✓ Connected to MongoDB and initialized index: {Config.COLLECTION_NAME}")
            except Exception as e:
                logger.warning(f"⚠ Could not initialize MongoDB index (might still be connecting): {e}")
            
        except Exception as e:
            logger.error(f"✗ Database connection error: {e}")

    
    def insert_event(self, event_data):
        """
        Insert a webhook event into the database.
        """
        try:
            # Ensure connected
            if not self.collection:
                self.connect()

            if not self.collection:
                raise ConnectionFailure("Could not connect to database")

            # Prepare document
            document = {
                "event_type": event_data.get("event_type"),
                "author": event_data.get("author"),
                "action": event_data.get("action", ""),
                "from_branch": event_data.get("from_branch", ""),
                "to_branch": event_data.get("to_branch", ""),
                "branch": event_data.get("branch", ""),
                "timestamp": datetime.fromisoformat(event_data.get("timestamp").replace('Z', '+00:00')),
                "request_id": event_data.get("request_id"),
                "created_at": datetime.now(timezone.utc)
            }
            
            # Insert into MongoDB
            result = self.collection.insert_one(document)
            logger.info(f"✓ Inserted event: {event_data.get('event_type')} by {event_data.get('author')}")
            return True
            
        except DuplicateKeyError:
            logger.warning(f"⚠ Duplicate event ignored: {event_data.get('request_id')}")
            return False
        except Exception as e:
            logger.error(f"✗ Error inserting event: {e}")
            raise
    
    def get_recent_events(self, limit=50, since=None):
        """
        Retrieve recent events from the database.
        """
        try:
            # Ensure connected
            if not self.collection:
                self.connect()
            
            # If still not connected (e.g. error in connect), return empty
            if not self.collection:
                return []

            # Build query filter
            query_filter = {}
            if since:
                query_filter["timestamp"] = {"$gt": since}
            
            # Fetch events sorted by timestamp (descending)
            events = list(
                self.collection.find(query_filter)
                .sort("timestamp", DESCENDING)
                .limit(limit)
            )
            
            # Convert ObjectId to string for JSON serialization
            for event in events:
                event["_id"] = str(event["_id"])
                # Convert datetime to ISO format string
                event["timestamp"] = event["timestamp"].isoformat()
                if "created_at" in event:
                    event["created_at"] = event["created_at"].isoformat()
            
            logger.info(f"✓ Retrieved {len(events)} events from database")
            return events
            
        except Exception as e:
            logger.error(f"✗ Error retrieving events: {e}")
            return []  # Return empty list on error to keep UI alive
    
    def get_all_events(self):
        """
        Get all events from the database.
        
        Returns:
            list: All events sorted by timestamp (newest first)
        """
        return self.get_recent_events(limit=1000)
    
    def clear_all_events(self):
        """
        Clear all events from the database.
        Useful for testing purposes.
        
        Returns:
            int: Number of documents deleted
        """
        try:
            result = self.collection.delete_many({})
            logger.info(f"✓ Cleared {result.deleted_count} events from database")
            return result.deleted_count
        except Exception as e:
            logger.error(f"✗ Error clearing events: {e}")
            raise
    
    def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("✓ MongoDB connection closed")


# Create a global database instance
db = Database()
