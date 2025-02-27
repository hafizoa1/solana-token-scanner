"""
Main entry point for the application.
"""
import asyncio
import logging
from app.bot.telegram_bot import TokenBot
from app.data.fetcher import DexScreenerFetcher
from app.classifiers.enhanced_meme_token_classifier import EnhancedMemeTokenClassifier
from app.classifiers.simple_rule_classifier import SimpleRuleClassifier
from app.services.token_service import TokenService
import app.config as config

def main():
    # Set up logging
    config.setup_logging()
    logger = logging.getLogger('Main')
    
    try:
        logger.info("Initializing application...")
        
        # Create dependencies
        fetcher = DexScreenerFetcher()
        
        # Choose classifier based on config
        if config.DEFAULT_CLASSIFIER.lower() == "simple":
            classifier = SimpleRuleClassifier()
        else:
            classifier = EnhancedMemeTokenClassifier()
        
        # Create service with dependencies
        token_service = TokenService(fetcher, classifier)
        
        # Create bot with service
        bot = TokenBot(
            token=config.BOT_TOKEN,
            chat_id=config.CHAT_ID,
            token_service=token_service
        )
        
        logger.info(f"Starting bot with classifier: {classifier.__class__.__name__}")
        bot.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()