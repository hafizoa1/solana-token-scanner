from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import logging
from typing import Optional

class TokenBot:
    def __init__(self, token: str, chat_id: str):
        """Initialize bot with token and chat ID"""
        self.token = token
        self.chat_id = chat_id
        self.application = Application.builder().token(token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("scan", self.scan_command))
        
        # Setup logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

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
            "Bot will also send automatic alerts for interesting tokens."
        )
        await update.message.reply_text(help_message)

    async def scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /scan command"""
        await update.message.reply_text("🔍 Starting token scan... Please wait.")
        
        try:
            # Here we'll later add the actual scanning logic
            # For now, just send a placeholder message
            result_message = (
                "Scan Results:\n\n"
                "This is a placeholder. Token scanning will be implemented soon!"
            )
            await update.message.reply_text(result_message)
        except Exception as e:
            error_message = f"❌ Error during scan: {str(e)}"
            await update.message.reply_text(error_message)

    async def send_message(self, message: str):
        """Send message to configured chat ID"""
        async with self.application.bot as bot:
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )

    def run(self):
        """Start the bot"""
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)