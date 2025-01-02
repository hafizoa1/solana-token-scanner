from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import logging
from typing import Optional
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
        """Handle /scan command"""
        await update.message.reply_text("🔍 Starting token scan... Please wait.")
        
        try:
            raw_tokens = await self.fetcher.get_validated_tokens()
            if not raw_tokens:
                await update.message.reply_text("No tokens found from DEX Screener.")
                return

            filtered_tokens = self.classifier.classify(raw_tokens)
            if not filtered_tokens:
                await update.message.reply_text("No tokens matched our criteria.")
                return
            
            # Send header
            await update.message.reply_text(f"🔎 Scan Results (Using {self.classifier.get_classifier_name()}):")
            
            # Send tokens in batches of 10
            for i in range(0, len(filtered_tokens), 10):
                batch = filtered_tokens[i:i+10]
                message = ""
                for j, token in enumerate(batch, i+1):
                    # Get token info from baseToken object
                    base_token = token.get('baseToken', {})
                    symbol = base_token.get('symbol', 'Unknown')
                    name = base_token.get('name', 'Unknown')
                    
                    message += (
                        f"{j}. {symbol} ({name})\n"
                        f"💰 Price: ${float(token.get('priceUsd', 0)):.4f}\n"
                        f"📈 24h Vol: ${float(token.get('volume', {}).get('h24', 0)):,.0f}\n"
                        f"💧 Liq: ${float(token.get('liquidity', {}).get('usd', 0)):,.0f}\n"
                        f"📊 24h: {float(token.get('priceChange', {}).get('h24', 0)):+.1f}%\n\n"
                    )
                await update.message.reply_text(message)
                
            # Send summary
            await update.message.reply_text(f"✅ Found {len(filtered_tokens)} matching tokens.")
                
        except Exception as e:
            error_message = f"❌ Error during scan: {str(e)}"
            logging.error(f"Scan error: {str(e)}")
            await update.message.reply_text(error_message)
            

    async def send_message(self, message: str):
        """Send message to configured chat ID"""
        async with self.application.bot as bot:
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )

   