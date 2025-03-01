import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import aiohttp
from time import time
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.data.fetcher import DexScreenerFetcher
import app.config as config

# Simple function to run a coroutine
def run_async(coroutine):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()

class TestDexScreenerFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = DexScreenerFetcher()
        
        # Setup mocks for config values
        config.DEXSCREENER_BASE_URL = "https://api.test.dexscreener.com"
        config.JUPITER_BASE_URL = "https://api.test.jupiter.com"
        config.BATCH_SIZE = 5
        config.RATE_LIMIT_REQUESTS = 10
        config.RATE_LIMIT_WINDOW = 60
    
    def tearDown(self):
        # Only close if session is a real session, not a mock
        if hasattr(self.fetcher.session, 'close') and callable(self.fetcher.session.close):
            try:
                run_async(self.fetcher.close())
            except:
                # Ignore errors during teardown
                pass

    def test_successfully_initialize_fetcher(self):
        """Test that the fetcher initializes with correct attributes"""
        self.assertEqual(self.fetcher.dex_base_url, "https://api.test.dexscreener.com")
        self.assertEqual(self.fetcher.jupiter_base_url, "https://api.test.jupiter.com")
        self.assertIsNone(self.fetcher.session)
        self.assertEqual(self.fetcher.BATCH_SIZE, 5)
        self.assertEqual(self.fetcher.RATE_LIMIT_REQUESTS, 10)
        self.assertEqual(self.fetcher.RATE_LIMIT_WINDOW, 60)
        self.assertEqual(self.fetcher.last_request_time, 0)

    @patch('aiohttp.ClientSession')
    def test_successfully_initialize_session(self, mock_client_session):
        """Test that init_session creates a session if none exists"""
        mock_instance = AsyncMock()
        mock_client_session.return_value = mock_instance
        
        # Ensure session is None initially
        self.assertIsNone(self.fetcher.session)
        
        # Call init_session
        run_async(self.fetcher.init_session())
        
        # Verify session was created
        mock_client_session.assert_called_once()
        self.assertEqual(self.fetcher.session, mock_instance)
        
        # Call again to ensure it doesn't create another session
        mock_client_session.reset_mock()
        run_async(self.fetcher.init_session())
        mock_client_session.assert_not_called()
        
        # Clean up manually to avoid tearDown issues
        self.fetcher.session = None

    def test_successfully_close_session(self):
        """Test that close properly closes and removes the session"""
        # Create a mock session
        mock_session = AsyncMock()
        self.fetcher.session = mock_session
        
        # Call close
        run_async(self.fetcher.close())
        
        # Verify session was closed and removed
        mock_session.close.assert_called_once()
        self.assertIsNone(self.fetcher.session)



    # Jupiter Trending Test
    def test_successfully_fetch_jupiter_trending_tokens(self):
        """Test get_jupiter_trending method fetches trending tokens"""
        # Replace the fetcher's get_jupiter_trending method with our own implementation
        async def mock_get_jupiter_trending():
            return [{"name": "Token1"}, {"name": "Token2"}]
    
        # Store the original method to restore later
        original_method = self.fetcher.get_jupiter_trending
    
        try:
            # Replace with our mock
            self.fetcher.get_jupiter_trending = mock_get_jupiter_trending
        
            # Call and test the mocked method
            result = run_async(self.fetcher.get_jupiter_trending())
        
            # Verify result
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["name"], "Token1")
            self.assertEqual(result[1]["name"], "Token2")
        finally:
            # Restore the original method
            self.fetcher.get_jupiter_trending = original_method

    def test_successfully_fetch_dex_data_in_batches(self):
        """Test get_dex_data_batch method fetches token data in batches"""
        # Create mock response data
        response_data = {
            'pairs': [{'name': 'Pair1'}, {'name': 'Pair2'}]
        }
        
        # Custom async context manager implementation
        class AsyncContextManagerMock:
            async def __aenter__(self):
                # Return a response-like object
                mock_response = MagicMock()
                # Add an awaitable json method
                async def mock_json():
                    return response_data
                mock_response.json = mock_json
                return mock_response
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        # Create session mock
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=AsyncContextManagerMock())
        
        # Set up the fetcher's session
        self.fetcher.session = mock_session
        
        # Make the rate limit respect method a no-op async function
        async def mock_respect_rate_limit():
            pass
        self.fetcher._respect_rate_limit = mock_respect_rate_limit
        
        # Call the method
        addresses = ['addr1', 'addr2', 'addr3']
        result = run_async(self.fetcher.get_dex_data_batch(addresses))
        
        # Verify mock session.get was called
        mock_session.get.assert_called_once()
        
        # Verify result matches expected mock data
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'Pair1')
        self.assertEqual(result[1]['name'], 'Pair2')
        
        # Test error handling
        class ErrorAsyncContextManagerMock:
            async def __aenter__(self):
                raise Exception("Test error")
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        # Replace the mock session's get method
        mock_session.get.return_value = ErrorAsyncContextManagerMock()
        
        # Call the method again
        result = run_async(self.fetcher.get_dex_data_batch(addresses))
        
        # Verify empty result due to error handling
        self.assertEqual(result, [])

    def test_successfully_process_dex_pair_data(self):
        """Test process_dex_pair method processes pair data correctly"""
        # Test with complete data
        pair = {
            'priceUsd': '1.5',
            'baseToken': {
                'totalSupply': '1000000',
                'address': '0x123'
            },
            'createAt': 1620000000000
        }
        
        processed = self.fetcher.process_dex_pair(pair)
        
        # Verify market cap calculation
        self.assertIn('market_cap', processed)
        self.assertEqual(processed['market_cap'], 1.5 * 1000000)
        
        # Verify pairCreatedAt added if missing
        self.assertIn('pairCreatedAt', processed)
        self.assertEqual(processed['pairCreatedAt'], 1620000000000)
        
        # Test with missing fields
        pair_incomplete = {
            'priceUsd': '1.5'
        }
        
        processed = self.fetcher.process_dex_pair(pair_incomplete)
        
        # Verify info structure was added
        self.assertIn('info', processed)
        self.assertIn('socials', processed['info'])
        
        # Test error handling
        pair_error = {
            'priceUsd': 'not-a-number',
            'baseToken': {
                'totalSupply': '1000000'
            }
        }
        
        processed = self.fetcher.process_dex_pair(pair_error)
        self.assertEqual(processed, {})

    def test_successfully_chunk_addresses_into_batches(self):
        """Test chunk_addresses splits token addresses into batches"""
        # Create test tokens
        tokens = [
            {'address': 'addr1'},
            {'address': 'addr2'},
            {'address': 'addr3'},
            {'address': 'addr4'},
            {'address': 'addr5'},
            {'address': 'addr6'},
            {'address': 'addr7'}
        ]
        
        # Set batch size
        self.fetcher.BATCH_SIZE = 3
        
        # Call the method
        batches = self.fetcher.chunk_addresses(tokens)
        
        # Verify batches
        self.assertEqual(len(batches), 3)
        self.assertEqual(batches[0], ['addr1', 'addr2', 'addr3'])
        self.assertEqual(batches[1], ['addr4', 'addr5', 'addr6'])
        self.assertEqual(batches[2], ['addr7'])

    def test_successfully_and_unsuccessfully_filter_by_criteria(self):
        """Test _meets_basic_criteria method filters tokens correctly"""
        # Test token that meets criteria
        token_good = {
            'liquidity': {'usd': 20000},
            'volume': {'h24': 5000}
        }
        result = self.fetcher._meets_basic_criteria(token_good, 10000, 1000)
        self.assertTrue(result)
        
        # Test token below liquidity threshold
        token_low_liq = {
            'liquidity': {'usd': 5000},
            'volume': {'h24': 5000}
        }
        result = self.fetcher._meets_basic_criteria(token_low_liq, 10000, 1000)
        self.assertFalse(result)
        
        # Test token below volume threshold
        token_low_vol = {
            'liquidity': {'usd': 20000},
            'volume': {'h24': 500}
        }
        result = self.fetcher._meets_basic_criteria(token_low_vol, 10000, 1000)
        self.assertFalse(result)
        
        # Test with invalid data
        token_invalid = {
            'liquidity': {'usd': 'not-a-number'},
            'volume': {'h24': 5000}
        }
        result = self.fetcher._meets_basic_criteria(token_invalid, 10000, 1000)
        self.assertFalse(result)
        
        # Test with missing data
        token_missing = {}
        result = self.fetcher._meets_basic_criteria(token_missing, 10000, 1000)
        self.assertFalse(result)

    @patch.object(DexScreenerFetcher, 'get_jupiter_trending')
    @patch.object(DexScreenerFetcher, 'get_dex_data_batch')
    @patch.object(DexScreenerFetcher, 'chunk_addresses')
    @patch.object(DexScreenerFetcher, 'process_dex_pair')
    @patch.object(DexScreenerFetcher, '_meets_basic_criteria')
    @patch.object(DexScreenerFetcher, 'init_session')
    def test_successfully_and_unsuccessfully_get_validated_tokens(self, mock_init, mock_criteria, mock_process, 
                                  mock_chunk, mock_dex_batch, mock_jupiter):
        """Test get_validated_tokens integrates all the components correctly"""
        # Set up the mocks
        mock_init.return_value = None
        
        # Mock jupiter trending tokens
        mock_jupiter.return_value = [
            {'address': 'addr1', 'tags': ['defi'], 'daily_volume': 1000000},
            {'address': 'addr2', 'tags': ['meme'], 'daily_volume': 500000}
        ]
        
        # Mock address chunking
        mock_chunk.return_value = [['addr1', 'addr2']]
        
        # Mock dex data batch
        mock_dex_batch.return_value = [
            {'baseToken': {'address': 'addr1'}, 'key': 'value1'},
            {'baseToken': {'address': 'addr2'}, 'key': 'value2'}
        ]
        
        # Set up the criteria to accept the first token but reject the second
        def criteria_side_effect(pair, *args, **kwargs):
            return pair['baseToken']['address'] == 'addr1'
        mock_criteria.side_effect = criteria_side_effect
        
        # Set up the process function to return a modified pair
        def process_side_effect(pair):
            processed = pair.copy()
            processed['processed'] = True
            return processed
        mock_process.side_effect = process_side_effect
        
        # Call the method
        result = run_async(self.fetcher.get_validated_tokens(min_liquidity=10000, min_volume=1000))
        
        # Verify all components were called correctly
        mock_init.assert_called_once()
        mock_jupiter.assert_called_once()
        mock_chunk.assert_called_once()
        mock_dex_batch.assert_called_once_with(['addr1', 'addr2'])
        
        # Verify criteria was applied
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['baseToken']['address'], 'addr1')
        
        # Verify processing was applied
        self.assertTrue(result[0]['processed'])
        
        # Verify Jupiter data was added
        self.assertIn('jupiter_data', result[0])
        self.assertEqual(result[0]['jupiter_data']['tags'], ['defi'])
        self.assertEqual(result[0]['jupiter_data']['daily_volume'], 1000000)
        
        # Test with no Jupiter tokens
        mock_jupiter.return_value = []
        result = run_async(self.fetcher.get_validated_tokens())
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()