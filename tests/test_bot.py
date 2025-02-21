import pytest
from app.bot.telegram_bot import TokenBot

def test_bot_initialization():
    bot = TokenBot("test_token", "test_chat_id")
    assert bot is not None
    assert bot.token == "test_token"
    assert bot.chat_id == "test_chat_id"