"""
Global configuration settings for the application.
"""
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# API Configurations
DEXSCREENER_BASE_URL = "https://api.dexscreener.com/latest/dex"
JUPITER_BASE_URL = "https://tokens.jup.ag"

# API Rate Limits
RATE_LIMIT_REQUESTS = 300
RATE_LIMIT_WINDOW = 60  # seconds

# Fetcher settings
BATCH_SIZE = 30
MIN_LIQUIDITY = float(os.getenv("MIN_LIQUIDITY", "100000"))  # $100k min liquidity 
MIN_VOLUME = float(os.getenv("MIN_VOLUME", "10000"))        # $10k min volume

# Telegram Bot settings
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TEST_TOKEN", "")  # Default to test token for local development
BOT_TOKEN_PROD = os.getenv("TELEGRAM_BOT_TOKEN", "")  # Production token for AWS

CHAT_ID = os.getenv("TELEGRAM_CHAT_TEST_ID", "")      # Default to test chat ID for local development
CHAT_ID_PROD = os.getenv("TELEGRAM_CHAT_ID", "")      # Production chat ID for AWS

# Determine if we're running in production (AWS Lambda) or local
IS_PRODUCTION = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

# Select the appropriate token and chat ID based on environment
ACTIVE_BOT_TOKEN = BOT_TOKEN_PROD if IS_PRODUCTION else BOT_TOKEN
ACTIVE_CHAT_ID = CHAT_ID_PROD if IS_PRODUCTION else CHAT_ID

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Classifier Configuration
DEFAULT_CLASSIFIER = os.getenv("DEFAULT_CLASSIFIER", "enhanced")

# Configure logging
def setup_logging():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT
    )