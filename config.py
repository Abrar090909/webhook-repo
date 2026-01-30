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
    PORT = int(os.getenv('PORT', 5000))
    HOST = '0.0.0.0'  # Allow external connections
    
    # Debug mode (only in development)
    DEBUG = FLASK_ENV == 'development'
    
    @staticmethod
    def validate():
        """
        Validate that all required configuration variables are set.
        Raises ValueError if any required config is missing.
        """
        if not Config.MONGODB_URI:
            raise ValueError("MONGODB_URI environment variable is not set!")
        
        if not Config.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable is not set!")
