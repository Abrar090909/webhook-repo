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
        """Initialize MongoDB connection."""
        self.client = None
        self.db = None
        self.collection = None
        self.connect()
    
    def connect(self):
        """
        Establish connection to MongoDB Atlas.
        Creates database and collection if they don't exist.
        """
        try:
            # Connect to MongoDB with timeout settings for Render deployment
            self.client = MongoClient(
                Config.MONGODB_URI,
                serverSelectionTimeoutMS=10000,  # 10 second timeout
                connectTimeoutMS=10000,  # 10 second connect timeout
                socketTimeoutMS=10000    # 10 second socket timeout
            )
            
            # Test the connection
            self.client.admin.command('ping')
            logger.info("✓ Successfully connected to MongoDB Atlas")
            
            # Get database and collection
            self.db = self.client[Config.DATABASE_NAME]
            self.collection = self.db[Config.COLLECTION_NAME]
            
            # Create unique index on request_id to prevent duplicates
            self.collection.create_index("request_id", unique=True)
            logger.info(f"✓ Using database: {Config.DATABASE_NAME}")
            logger.info(f"✓ Using collection: {Config.COLLECTION_NAME}")
            
        except ConnectionFailure as e:
            logger.error(f"✗ Failed to connect to MongoDB: {e}")
            raise
    
    def insert_event(self, event_data):
        """
        Insert a webhook event into the database.
        Prevents duplicate entries using request_id.
        
        Args:
            event_data (dict): Event data containing:
                - event_type: "push", "pull_request", or "merge"
                - author: GitHub username
                - action: Action performed (for PRs)
                - from_branch: Source branch (for PRs/merges)
                - to_branch: Target branch (for PRs/merges)
                - branch: Branch name (for pushes)
                - timestamp: ISO 8601 timestamp
                - request_id: Unique identifier
        
        Returns:
            bool: True if inserted successfully, False if duplicate
        """
        try:
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
        
        Args:
            limit (int): Maximum number of events to return
            since (datetime): Only return events after this timestamp
        
        Returns:
            list: List of event documents sorted by timestamp (newest first)
        """
        try:
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
            raise
    
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
