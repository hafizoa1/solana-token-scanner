from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import logging
from typing import Optional
import asyncio 
from app.data.fetcher import DexScreenerFetcher  # Adjust the import path as necessary
from app.classifiers.simple_rule_classifier import SimpleRuleClassifier  # Adjust the import path as necessary

class TokenBot:
    def __init__(self, token: str, chat_id: str):
        """Initialize bot with token and chat ID"""
        self.token = token
        self.chat_id = chat_id
        self.application = Application.builder().token(token).build()
        self.fetcher = DexScreenerFetcher()
        self.classifier = SimpleRuleClassifier()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("scan", self.scan_command))
        
        # Setup logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

    def run(self):
        """Non-async method to start the bot"""
        print("Starting bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

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
        help_message = (
            "🤖 Bot Commands:\n\n"
            "/scan - Start a new token scan\n"
            "/help - Show this help message\n\n"
            "Using classifier: " + self.classifier.get_classifier_name() + "\n"
            "Bot will also send automatic alerts for interesting tokens."
        )
        await update.message.reply_text(help_message)

    async def scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔍 Starting scan...")
        
        try:
            raw_tokens = await self.fetcher.get_validated_tokens()
            if not raw_tokens:
                return await update.message.reply_text("No tokens found.")

            filtered_tokens = self.classifier.classify(raw_tokens)
            if not filtered_tokens:
                return await update.message.reply_text("No matches found.")

            message_batches = []
            current_batch = []

            for i, token in enumerate(filtered_tokens, 1):
                base_token = token.get('baseToken', {})
                token_info = (
                    f"{i}. {base_token.get('symbol', 'Unknown')} ({base_token.get('name', 'Unknown')})\n"
                    f"💰 Price: ${float(token.get('priceUsd', 0)):.4f}\n"
                    f"📈 24h Vol: ${float(token.get('volume', {}).get('h24', 0)):,.0f}\n"
                    f"💧 Liq: ${float(token.get('liquidity', {}).get('usd', 0)):,.0f}\n"
                    f"📊 24h: {float(token.get('priceChange', {}).get('h24', 0)):+.1f}%\n"
                )
                
                current_batch.append(token_info)
            
                if len(current_batch) == 10:
                    batch_message = ''.join(current_batch)
                    message_batches.append(batch_message)
                    current_batch = []

            if current_batch:
                batch_message = ''.join(current_batch)
                message_batches.append(batch_message)

            # Send batches in parallel but wait for each group
            for batch in message_batches:
                await update.message.reply_text(batch)
                await asyncio.sleep(0.5) 

            await update.message.reply_text(f"✅ Found {len(filtered_tokens)} tokens.")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def send_message(self, message: str):
        """Send message to configured chat ID"""
        async with self.application.bot as bot:
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )

   