import json
import os
from app.bot.telegram_bot import TokenBot

def lambda_handler(event, context):
    """AWS Lambda entry point - runs bot instance and processes webhook commands."""
    
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        return {
            'statusCode': 500,
            'body': json.dumps('Error: Missing environment variables')
        }

    bot = TokenBot(token, chat_id)  # Instantiate bot

    if 'body' in event:
        # Handle Telegram webhook events
        body = json.loads(event['body'])
        message = body.get('message', {}).get('text', '')

        if message == "/scan":
            response = bot.scan_command(None, None)  # Process /scan command
            return {
                'statusCode': 200,
                'body': json.dumps({"message": "Scan completed", "response": response})
            }

    # If triggered manually (e.g., AWS Scheduler), just start bot actions
    bot.run()

    return {
        'statusCode': 200,
        'body': json.dumps('Bot started successfully')
    }