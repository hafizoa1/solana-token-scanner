import os
from dotenv import load_dotenv
from app.bot.telegram_bot import TokenBot
from apscheduler.schedulers.background import BlockingScheduler

def run_bot():
    token = os.getenv('TELEGRAM_BOT_TEST_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_TEST_ID')
    
    if not token or not chat_id:
        print("Error: Missing env variables")
        return
        
    bot = TokenBot(token, chat_id)
    bot.run()

def main():
    load_dotenv()
    scheduler = BlockingScheduler()  # Changed to BlockingScheduler
    scheduler.add_job(run_bot, 'cron', hour='0,12')
    
    try:
        run_bot()  # Run immediately
        scheduler.start()  # Start scheduler for future runs
    except KeyboardInterrupt:
        scheduler.shutdown()
        print("\nBot stopped")

if __name__ == "__main__":
    main()