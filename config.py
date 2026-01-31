"""
Configuration module for the webhook application.
Manages environment variables and application settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""
    
    # MongoDB Configuration
    # MongoDB connection string from environment variable
    MONGODB_URI = os.getenv('MONGODB_URI')
    
    # Database and collection names
    DATABASE_NAME = 'github_webhooks'
    COLLECTION_NAME = 'events'
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Server Configuration
    _port = os.getenv('PORT', '5000')
    try:
        PORT = int(_port)
    except (ValueError, TypeError):
        PORT = 5000
    HOST = '0.0.0.0'  # Allow external connections
    
    # Debug mode (only in development)
    DEBUG = FLASK_ENV == 'development'
    
    @staticmethod
    def validate():
        """
        Validate that all required configuration variables are set.
        Logs warnings if missing but doesn't crash the app.
        """
        missing = []
        if not Config.MONGODB_URI:
            missing.append("MONGODB_URI")
        
        if not Config.SECRET_KEY or Config.SECRET_KEY == 'dev-secret-key':
            missing.append("SECRET_KEY")
            
        if missing:
            print(f"⚠️  Missing or default environment variables: {', '.join(missing)}")
            print("Note: App will start but database operations will fail.")
            return False
        return True
