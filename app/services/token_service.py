"""
Service layer for token operations, handling business logic.
"""
from typing import Dict, List, Any
import logging
import asyncio
from app.data.fetcher import DexScreenerFetcher
from app.classifiers.base import TokenClassifier as BaseClassifier
import app.config as config

class TokenService:
    def __init__(self, fetcher: DexScreenerFetcher, classifier: BaseClassifier):
        """Initialize with dependencies injected"""
        self.fetcher = fetcher
        self.classifier = classifier
        self.logger = logging.getLogger('TokenService')
    
    async def scan_tokens(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Main business logic for scanning tokens.
        Returns categorized tokens.
        """
        try:
            # Get tokens from fetcher with config parameters
            self.logger.info("Fetching validated tokens")
            raw_tokens = await self.fetcher.get_validated_tokens(
                min_liquidity=config.MIN_LIQUIDITY, 
                min_volume=config.MIN_VOLUME
            )
            
            if not raw_tokens:
                self.logger.warning("No tokens found")
                return {}
            
            # Classify tokens
            self.logger.info(f"Classifying {len(raw_tokens)} tokens")
            categorized_tokens = self.classifier.classify(raw_tokens)
            
            # Log results
            total_tokens = sum(len(tokens) for tokens in categorized_tokens.values())
            self.logger.info(f"Found {total_tokens} tokens across {len([c for c, t in categorized_tokens.items() if t])} categories")
            
            return categorized_tokens
            
        except Exception as e:
            self.logger.error(f"Error during token scan: {str(e)}")
            raise
    

    
    async def shutdown(self):
        """Clean up resources"""
        if hasattr(self.fetcher, 'close'):
            await self.fetcher.close()