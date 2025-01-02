# main.py
import os
from dotenv import load_dotenv
from app.bot.telegram_bot import TokenBot

def main():
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("Error: Missing required environment variables")
        return
        
    try:
        bot = TokenBot(token, chat_id)
        bot.run()  # Using non-async run method
    except KeyboardInterrupt:
        print("\nBot stopped")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()