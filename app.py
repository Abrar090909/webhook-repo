"""
Flask Webhook Receiver Application
Receives GitHub webhook events and stores them in MongoDB.
Provides a UI dashboard for real-time event monitoring.
"""

from flask import Flask, request, jsonify, render_template
from datetime import datetime, timezone
import uuid
import logging
from config import Config
from database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Validate configuration on startup
Config.validate()


@app.route('/')
def index():
    """
    Serve the main dashboard UI.
    
    Returns:
        HTML: Dashboard page
    """
    return render_template('index.html')


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook receiver endpoint for GitHub Actions.
    
    Expected JSON payload format:
    {
        "event_type": "push" | "pull_request" | "merge",
        "author": "username",
        "action": "opened" | "closed" | etc. (for pull_request),
        "from_branch": "source-branch" (for pull_request/merge),
        "to_branch": "target-branch" (for pull_request/merge),
        "branch": "branch-name" (for push),
        "timestamp": "2026-01-30T10:00:00Z",
        "request_id": "unique-id" (optional, auto-generated if missing)
    }
    
    Returns:
        JSON: Success or error message with HTTP status code
    """
    try:
        # Parse JSON payload
        data = request.get_json()
        
        if not data:
            logger.warning("⚠ Received empty webhook payload")
            return jsonify({"error": "Empty payload"}), 400
        
        # Validate required fields
        required_fields = ['event_type', 'author', 'timestamp']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            logger.warning(f"⚠ Missing required fields: {missing_fields}")
            return jsonify({"error": f"Missing fields: {missing_fields}"}), 400
        
        # Generate unique request_id if not provided
        if 'request_id' not in data:
            data['request_id'] = str(uuid.uuid4())
        
        # Log received webhook
        logger.info(f"📥 Received {data['event_type']} webhook from {data['author']}")
        
        # Store event in MongoDB
        success = db.insert_event(data)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Event stored successfully",
                "request_id": data['request_id']
            }), 201
        else:
            return jsonify({
                "status": "duplicate",
                "message": "Event already exists (duplicate ignored)",
                "request_id": data['request_id']
            }), 200
            
    except Exception as e:
        logger.error(f"✗ Error processing webhook: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/events', methods=['GET'])
def get_events():
    """
    API endpoint to fetch recent events for the dashboard.
    Supports optional 'since' query parameter for incremental updates.
    
    Query Parameters:
        since (str): ISO 8601 timestamp to fetch events after this time
        limit (int): Maximum number of events to return (default: 50)
    
    Returns:
        JSON: List of events with metadata
    """
    try:
        # Get query parameters
        since_param = request.args.get('since')
        limit = request.args.get('limit', 50, type=int)
        
        # Parse 'since' timestamp if provided
        since = None
        if since_param:
            try:
                since = datetime.fromisoformat(since_param.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"⚠ Invalid 'since' parameter: {since_param}")
        
        # Fetch events from database
        events = db.get_recent_events(limit=limit, since=since)
        
        logger.info(f"📤 Sent {len(events)} events to dashboard")
        
        return jsonify({
            "status": "success",
            "count": len(events),
            "events": events,
            "server_time": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"✗ Error fetching events: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/clear', methods=['POST'])
def clear_events():
    """
    API endpoint to clear all events from the database.
    Useful for testing purposes.
    
    Returns:
        JSON: Number of events deleted
    """
    try:
        count = db.clear_all_events()
        logger.info(f"🗑️  Cleared {count} events")
        
        return jsonify({
            "status": "success",
            "message": f"Cleared {count} events",
            "deleted_count": count
        }), 200
        
    except Exception as e:
        logger.error(f"✗ Error clearing events: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring and deployment.
    """
    try:
        # Ensure we try to connect if not already
        if not db.client:
            db.connect()
            
        # Test database connection if client exists
        if db.client:
            db.client.admin.command('ping')
            db_status = "connected"
        else:
            db_status = "initialization_failed"
        
        return jsonify({
            "status": "healthy",
            "database": db_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.warning(f"⚠ Health check database ping failed: {e}")
        # Still return 200/healthy for the app itself if the DB is just slow
        # This prevents Render from killing the app during DB cold starts
        return jsonify({
            "status": "healthy",
            "database": "connecting_or_failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "App is running, database is slow/connecting"
        }), 200


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"✗ Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    """Run the Flask application."""
    logger.info("🚀 Starting GitHub Webhook Receiver")
    logger.info(f"🌐 Running on http://{Config.HOST}:{Config.PORT}")
    
    # Run the app
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
