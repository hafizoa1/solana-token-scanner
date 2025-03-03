from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import logging
from typing import Optional, List, Dict, Any
import asyncio 
from app.services.token_service import TokenService
import app.config as config

class TokenBot:
    def __init__(self, token: str, chat_id: str, token_service: TokenService):
        """Initialize bot with token, chat ID, and service dependency"""
        self.token = token
        self.chat_id = chat_id
        self.application = Application.builder().token(token).build()
        self.token_service = token_service
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("scan", self.scan_command))
        
        # Setup logging
        self.logger = logging.getLogger('TokenBot')

    def run(self):
        """Non-async method to start the bot"""
        self.logger.info("Starting bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    def scan_command_sync(self, update: Update, context: Optional[ContextTypes.DEFAULT_TYPE] = None):
        """Synchronous wrapper for scan_command"""
        async def run_scan():
            # Explicitly pass the update and context
            await self.scan_command(update, context)
        
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the async method
            self.logger.info("Starting synchronous scan wrapper")
            loop.run_until_complete(run_scan())
            self.logger.info("Synchronous scan completed successfully")
        except Exception as e:
            self.logger.error(f"Error in synchronous scan wrapper: {e}")
            # You might want to send an error message to the user here
            raise
        finally:
            # Close the event loop
            loop.close()
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /start command"""
        welcome_message = (
            "👋 Welcome to the Solana Token Scanner!\n\n"
            "Available commands:\n"
            "/scan - Scan for new token opportunities\n"
            "/help - Show this help message"
        )
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /help command"""
        classifier_name = "Unknown"
        if hasattr(self.token_service.classifier, 'get_classifier_name'):
            classifier_name = self.token_service.classifier.get_classifier_name()
            
        help_message = (
            "🤖 Bot Commands:\n\n"
            "/scan - Start a new token scan\n"
            "/help - Show this help message\n\n"
            f"Using classifier: {classifier_name}\n"
            "Bot will also send automatic alerts for interesting tokens."
        )
        await update.message.reply_text(help_message)

    async def scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /scan command"""
        await update.message.reply_text("🔍 Starting scan...")
    
        try:
            # Get categorized tokens from the service
            categorized_tokens = await self.token_service.scan_tokens()
            
            # Check if any tokens were found
            if not categorized_tokens:
                return await update.message.reply_text("No tokens found.")
                
            # Check if any categories have tokens
            total_tokens = sum(len(tokens) for tokens in categorized_tokens.values())
            if total_tokens == 0:
                return await update.message.reply_text("No matches found.")
            
            # Format and send results
            await self._send_categorized_tokens(update, categorized_tokens)
            
        except Exception as e:
            self.logger.error(f"Error during scan: {str(e)}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def _send_categorized_tokens(self, update: Update, categorized_tokens: Dict[str, List[Dict[str, Any]]]):
        """Format and send categorized tokens to the user"""
        # Category descriptions
        category_descriptions = {
            'Moonshot': "Tokens with high potential for explosive growth 🚀",
            'Solid Investment': "Tokens with strong fundamentals and steady growth potential 💪",
            'Risky': "Tokens that meet basic criteria but require caution ⚠️",
            'Potential': "Tokens showing promise in specific areas, worth watching 👀"
        }
        
        # Count total tokens and categories with tokens
        total_tokens = sum(len(tokens) for tokens in categorized_tokens.values())
        categories_with_tokens = len([c for c, t in categorized_tokens.items() if t])
        
        # Send results for each category
        for category, tokens in categorized_tokens.items():
            if not tokens:
                continue  # Skip empty categories
            
            # Send category header with description
            description = category_descriptions.get(category, "")
            await update.message.reply_text(f"📊 *{category}* - {description}\n({len(tokens)} tokens)", parse_mode='Markdown')
            
            message_batches = []
            current_batch = []
            
            for i, token in enumerate(tokens, 1):
                base_token = token.get('baseToken', {})
                token_info = (
                    f"{i}. {base_token.get('symbol', 'Unknown')} ({base_token.get('name', 'Unknown')})\n"
                    f"💰 Price: ${float(token.get('priceUsd', 0)):.4f}\n"
                    f"📈 24h Vol: ${float(token.get('volume', {}).get('h24', 0)):,.0f}\n"
                    f"💧 Liq: ${float(token.get('liquidity', {}).get('usd', 0)):,.0f}\n"
                    f"📊 24h: {float(token.get('priceChange', {}).get('h24', 0)):+.1f}%\n"
                )
                
                # Add score if available
                if 'score' in token:
                    token_info += f"⭐ Score: {token['score']:.1f}/10\n\n"
                else:
                    token_info += "\n"
                
                current_batch.append(token_info)
                
                if len(current_batch) == 10:
                    batch_message = ''.join(current_batch)
                    message_batches.append(batch_message)
                    current_batch = []
                    
            if current_batch:
                batch_message = ''.join(current_batch)
                message_batches.append(batch_message)
                
            # Send batches for this category
            for batch in message_batches:
                await update.message.reply_text(batch)
                await asyncio.sleep(0.5)
        
        await update.message.reply_text(f"✅ Found {total_tokens} tokens across {categories_with_tokens} categories.")