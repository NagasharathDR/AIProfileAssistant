# Configuration settings for the application

import os

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_default_secret_key')
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///default.db')
    # Add other configuration variables as needed

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///dev.db')

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///test.db')

class ProductionConfig(Config):
    """Production configuration."""
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///prod.db')