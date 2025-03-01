import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
import logging
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.token_service import TokenService
from app.bot.telegram_bot import TokenBot

# Simple function to run a coroutine
def run_async(coroutine):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()

class TestTokenBot(unittest.TestCase):
    def setUp(self):
        # Create mocks
        self.mock_token_service = MagicMock(spec=TokenService)
        self.mock_token_service.classifier = MagicMock()
        self.mock_token_service.classifier.get_classifier_name = MagicMock(return_value="Test Classifier")
        
        # Mock the Application builder
        with patch('telegram.ext.Application.builder') as mock_builder:
            mock_app = MagicMock()
            mock_builder.return_value.token.return_value.build.return_value = mock_app
            
            # Create the bot instance
            self.bot = TokenBot(
                token="test_token",
                chat_id="test_chat_id",
                token_service=self.mock_token_service
            )
            
            # Save the mock application for assertions
            self.mock_app = mock_app

    def test_successfully_initialize_bot(self):
        """Test that the bot initializes correctly with proper handlers"""
        # Check if handlers were added
        self.assertEqual(self.mock_app.add_handler.call_count, 3)
        
        # Verify token and chat_id were set
        self.assertEqual(self.bot.token, "test_token")
        self.assertEqual(self.bot.chat_id, "test_chat_id")
        
        # Verify the token_service was set
        self.assertEqual(self.bot.token_service, self.mock_token_service)

    def test_successfully_run_polling(self):
        """Test the run method starts polling"""
        # Call the run method
        self.bot.run()
        
        # Verify that run_polling was called with expected args
        self.mock_app.run_polling.assert_called_once()
        call_args = self.mock_app.run_polling.call_args[1]
        self.assertIn('allowed_updates', call_args)
        self.assertEqual(call_args['allowed_updates'], Update.ALL_TYPES)

    @patch('asyncio.new_event_loop')
    @patch('asyncio.set_event_loop')
    def test_successfully_wrap_async_scan_command(self, mock_set_event_loop, mock_new_event_loop):
        """Test that scan_command_sync properly wraps the async method"""
        # Setup mocks
        mock_loop = MagicMock()
        mock_new_event_loop.return_value = mock_loop
        
        # Set up mock update and context
        mock_update = MagicMock(spec=Update)
        mock_context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        # Patch the scan_command to be a mock
        self.bot.scan_command = AsyncMock()
        
        # Call the wrapper
        self.bot.scan_command_sync(mock_update, mock_context)
        
        # Verify event loop was created and used
        mock_new_event_loop.assert_called_once()
        mock_set_event_loop.assert_called_once_with(mock_loop)
        mock_loop.run_until_complete.assert_called_once()
        mock_loop.close.assert_called_once()
        
        # Get the coroutine function that was passed to run_until_complete
        coro_func = mock_loop.run_until_complete.call_args[0][0]
        
        # Execute the coroutine function directly
        # This is a workaround since we can't easily run the coroutine in a test
        mock_loop.run_until_complete.side_effect = lambda coro: coro.send(None)
        
        try:
            # This should trigger the first part of the coroutine execution
            # which will call scan_command
            mock_loop.run_until_complete(coro_func)
        except StopIteration:
            # Expected when we manually step through the coroutine
            pass
        
        # Now verify scan_command was called with the right parameters
        self.bot.scan_command.assert_called_once_with(mock_update, mock_context)

    def test_successfully_send_categorized_tokens(self):
        """Test the _send_categorized_tokens method formats and sends tokens correctly"""
        # Create a mock update
        mock_update = MagicMock(spec=Update)
        mock_update.message.reply_text = AsyncMock()
        
        # Create test data
        categorized_tokens = {
            'Moonshot': [
                {
                    'baseToken': {'symbol': 'MOON', 'name': 'MoonToken'},
                    'priceUsd': '0.12345',
                    'volume': {'h24': '500000'},
                    'liquidity': {'usd': '200000'},
                    'priceChange': {'h24': 15.5},
                    'score': 9.2
                }
            ],
            'Solid Investment': [],
            'Risky': [],
            'Potential': []
        }
        
        # Call the method using run_async
        run_async(self.bot._send_categorized_tokens(mock_update, categorized_tokens))
        
        # Verify the results
        # Should have 3 calls: category header, token batch, and summary
        self.assertEqual(mock_update.message.reply_text.call_count, 3)
        
        # Verify category header was sent
        first_call_args = mock_update.message.reply_text.call_args_list[0][0]
        self.assertIn('Moonshot', first_call_args[0])
        self.assertIn('(1 tokens)', first_call_args[0])
        
        # Verify token information was sent
        second_call_args = mock_update.message.reply_text.call_args_list[1][0]
        token_info = second_call_args[0]
        self.assertIn('MOON', token_info)
        self.assertIn('$0.1235', token_info)  # Price formatted
        self.assertIn('$500,000', token_info)  # Volume formatted
        self.assertIn('$200,000', token_info)  # Liquidity formatted
        self.assertIn('+15.5%', token_info)    # Price change formatted
        self.assertIn('9.2/10', token_info)    # Score included
        
        # Verify summary was sent
        third_call_args = mock_update.message.reply_text.call_args_list[2][0]
        summary = third_call_args[0]
        self.assertIn('Found 1 tokens', summary)
        self.assertIn('1 categories', summary)

    def test_unsuccessfully_scan_with_no_tokens(self):
        """Test scan_command when no tokens are found"""
        # Set up mocks
        mock_update = MagicMock(spec=Update)
        mock_update.message.reply_text = AsyncMock()
        mock_context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        # Configure token_service to return empty categorized tokens
        self.mock_token_service.scan_tokens = AsyncMock(return_value={})
        
        # Call the method using run_async
        run_async(self.bot.scan_command(mock_update, mock_context))
        
        # Verify response
        mock_update.message.reply_text.assert_any_call("🔍 Starting scan...")
        mock_update.message.reply_text.assert_any_call("No tokens found.")
        
    def test_unsuccessfully_scan_with_error(self):
        """Test scan_command when an error occurs"""
        # Set up mocks
        mock_update = MagicMock(spec=Update)
        mock_update.message.reply_text = AsyncMock()
        mock_context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        # Configure token_service to raise an exception
        self.mock_token_service.scan_tokens = AsyncMock(side_effect=Exception("Test error"))
        
        # Call the method using run_async
        run_async(self.bot.scan_command(mock_update, mock_context))
        
        # Verify response
        mock_update.message.reply_text.assert_any_call("🔍 Starting scan...")
        mock_update.message.reply_text.assert_any_call("❌ Error: Test error")

    def test_successfully_display_help_command(self):
        """Test help_command response format"""
        # Set up mocks
        mock_update = MagicMock(spec=Update)
        mock_update.message.reply_text = AsyncMock()
        mock_context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        # Call the method using run_async
        run_async(self.bot.help_command(mock_update, mock_context))
        
        # Verify help message contains the classifier name and expected commands
        call_args = mock_update.message.reply_text.call_args[0]
        help_message = call_args[0]
        self.assertIn("Test Classifier", help_message)
        self.assertIn("/scan", help_message)
        self.assertIn("/help", help_message)


if __name__ == '__main__':
    unittest.main()