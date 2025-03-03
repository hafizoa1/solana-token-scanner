import aiohttp
from typing import Dict, List, Optional
from decimal import Decimal
import logging
import asyncio
from time import time
import app.config as config

class DexScreenerFetcher:
    def __init__(self):
        self.dex_base_url = config.DEXSCREENER_BASE_URL
        self.jupiter_base_url = config.JUPITER_BASE_URL
        self.session = None
        self.logger = logging.getLogger('DexScreener')
        self.last_request_time = 0
        self.BATCH_SIZE = config.BATCH_SIZE
        self.RATE_LIMIT_REQUESTS = config.RATE_LIMIT_REQUESTS
        self.RATE_LIMIT_WINDOW = config.RATE_LIMIT_WINDOW
   
    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
   
    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def _respect_rate_limit(self):
        current_time = time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < (self.RATE_LIMIT_WINDOW / self.RATE_LIMIT_REQUESTS):
            await asyncio.sleep((self.RATE_LIMIT_WINDOW / self.RATE_LIMIT_REQUESTS) - time_since_last)
        self.last_request_time = time()

    async def get_jupiter_trending(self) -> List[Dict]:
        """Get trending tokens from Jupiter"""
        await self.init_session()
        try:
            url = f"{self.jupiter_base_url}/tokens"
            params = {'tags': 'birdeye-trending'}
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                self.logger.info(f"Found {len(data)} trending tokens on Jupiter")
                return data
        except Exception as e:
            self.logger.error(f"Error fetching Jupiter trending: {str(e)}")
            return []

    async def get_dex_data_batch(self, addresses: List[str]) -> List[Dict]:
        """Get full DexScreener data for batch of addresses"""
        await self._respect_rate_limit()
        try:
            addresses_str = ','.join(addresses)
            url = f"{self.dex_base_url}/tokens/{addresses_str}"
            async with self.session.get(url) as response:
                data = await response.json()
                return data.get('pairs', [])
        except Exception as e:
            self.logger.error(f"Error fetching DexScreener batch: {str(e)}")
            return []

    def process_dex_pair(self, pair: Dict) -> Dict:
        """Process DexScreener pair data while maintaining original format"""
        try:
            # Keep original DexScreener format but add calculated fields
            processed_pair = pair.copy()
            
            # Calculate market cap if possible
            if (price := float(pair.get('priceUsd', 0))) and \
               (supply := float(pair.get('baseToken', {}).get('totalSupply', 0))):
                processed_pair['market_cap'] = price * supply

            # Ensure required fields exist
            if 'pairCreatedAt' not in processed_pair:
                processed_pair['pairCreatedAt'] = pair.get('createAt', 0)

            # Add default socials structure if not present
            if 'info' not in processed_pair:
                processed_pair['info'] = {'socials': []}

            return processed_pair
        except Exception as e:
            self.logger.error(f"Error processing pair data: {str(e)}")
            return {}

    def chunk_addresses(self, tokens: List[Dict]) -> List[List[str]]:
        """Split Jupiter tokens into address batches"""
        addresses = [token['address'] for token in tokens]
        return [addresses[i:i + self.BATCH_SIZE] 
                for i in range(0, len(addresses), self.BATCH_SIZE)]

    async def get_validated_tokens(self, min_liquidity: float = 10000, min_volume: float = 1000) -> List[Dict]:
        """Get validated tokens from Jupiter and DexScreener"""
        await self.init_session()
        # Get trending tokens from Jupiter
        jupiter_tokens = await self.get_jupiter_trending()
        validated_tokens = []

        if not jupiter_tokens:
            return []

        # Process in batches
        address_batches = self.chunk_addresses(jupiter_tokens)
        
        for batch in address_batches:
            self.logger.info(f"Processing batch of {len(batch)} tokens...")
            dex_pairs = await self.get_dex_data_batch(batch)
            
            # Process each pair and maintain DexScreener format
            for pair in dex_pairs:
                if self._meets_basic_criteria(pair, min_liquidity, min_volume):
                    processed_pair = self.process_dex_pair(pair)
                    if processed_pair:
                        # Add Jupiter data as additional information
                        jupiter_token = next(
                            (t for t in jupiter_tokens if t['address'].lower() == 
                             pair.get('baseToken', {}).get('address', '').lower()),
                            None
                        )
                        if jupiter_token:
                            processed_pair['jupiter_data'] = {
                                'tags': jupiter_token.get('tags', []),
                                'daily_volume': jupiter_token.get('daily_volume', 0)
                            }
                        validated_tokens.append(processed_pair)

        return validated_tokens

    def _meets_basic_criteria(self, pair: Dict, min_liquidity: float, min_volume: float) -> bool:
        """Check if pair meets basic quality criteria"""
        try:
            liquidity = float(pair.get('liquidity', {}).get('usd', 0))
            volume = float(pair.get('volume', {}).get('h24', 0))
            return liquidity >= min_liquidity and volume >= min_volume
        except (TypeError, ValueError):
            return False