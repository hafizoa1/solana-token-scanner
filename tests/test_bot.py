import pytest
from unittest.mock import MagicMock
from app.bot.telegram_bot import TokenBot
from app.services.token_service import TokenService

def test_bot_initialization():
    # Create a mock for the token service
    mock_service = MagicMock(spec=TokenService)
    
    # Initialize the bot with the mock service
    bot = TokenBot("test_token", "test_chat_id", mock_service)
    
    # Assert that the bot was initialized correctly
    assert bot.token == "test_token"
    assert bot.chat_id == "test_chat_id"
    assert bot.token_service == mock_service