"""Configuration settings for the BDD Demo project."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for application settings."""
    
    # Database settings
    USE_SQL_SERVER = os.getenv('USE_SQL_SERVER', 'false').lower() == 'true'
    SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'data/demo.db')
    SQL_SERVER_CONNECTION = os.getenv('SQL_SERVER_CONNECTION', '')
    
    # AWS Bedrock settings (mocked)
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'mock-key')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', 'mock-secret')
    BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
    
    # Jira Xray settings (mocked)
    JIRA_BASE_URL = os.getenv('JIRA_BASE_URL', 'https://your-company.atlassian.net')
    JIRA_USERNAME = os.getenv('JIRA_USERNAME', 'mock-user')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN', 'mock-token')
    XRAY_PROJECT_KEY = os.getenv('XRAY_PROJECT_KEY', 'DEMO')
    
    # Application settings
    MOCK_MODE = os.getenv('MOCK_MODE', 'true').lower() == 'true'
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
    SCREENSHOTS_DIR = 'screenshots'
    REPORTS_DIR = 'reports'
    FEATURES_DIR = 'features'
    
    # FastAPI mock server settings
    FASTAPI_HOST = os.getenv('FASTAPI_HOST', '127.0.0.1')
    FASTAPI_PORT = int(os.getenv('FASTAPI_PORT', '8001'))
    
    # Selenium settings
    SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'true').lower() == 'true'
    SELENIUM_TIMEOUT = int(os.getenv('SELENIUM_TIMEOUT', '10'))
    
    @classmethod
    def get_db_connection_string(cls):
        """Get database connection string based on configuration."""
        if cls.USE_SQL_SERVER:
            return cls.SQL_SERVER_CONNECTION
        else:
            return f"sqlite:///{cls.SQLITE_DB_PATH}"
