import json
import logging
import traceback
import base64
import os
import requests
import asyncio
from telegram import Update
from app.bot.telegram_bot import TokenBot

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

def lambda_handler(event, context):
    try:
        logger.info("Lambda function invoked")
        
        # Extract and decode the body if it's base64 encoded
        body = event.get('body')
        is_base64 = event.get('isBase64Encoded', False)
        
        if is_base64 and body:
            logger.info("Decoding base64 body")
            body_bytes = base64.b64decode(body)
            body = body_bytes.decode('utf-8')
        
        # Parse the JSON body
        if not body:
            logger.error("No body in request")
            return {'statusCode': 400, 'body': json.dumps({"error": "No body in request"})}
            
        telegram_update = json.loads(body)
        
        # Extract message data
        message = telegram_update.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        
        logger.info(f"Message: '{text}', Chat ID: {chat_id}")
        
        # Check if this is the scan command
        if text and text.startswith('/scan'):
            logger.info("Detected /scan command")
            
            # Send a simple response to acknowledge receipt
            send_telegram_message(chat_id, "🔍 Starting scan...")
            
            # Process the scan command in a separate function
            asyncio.run(process_scan_command(telegram_update, chat_id))
        
        return {'statusCode': 200, 'body': json.dumps({"status": "success"})}
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}

async def process_scan_command(telegram_update, chat_id):
    """Process the scan command using the TokenBot class"""
    try:
        # Create a bot instance for this request
        bot = TokenBot(TELEGRAM_BOT_TOKEN, chat_id)
        
        # Create an Update object that the scan_command expects
        update = Update.de_json(telegram_update, None)
        
        # Call the scan_command directly - this handles all the scanning logic
        await bot.scan_command(update, None)
        
        logger.info("Scan command processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing scan command: {str(e)}")
        logger.error(traceback.format_exc())
        send_telegram_message(chat_id, f"❌ Error: {str(e)}")

def send_telegram_message(chat_id, text):
    """Send a simple message via Telegram API directly"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    
    try:
        response = requests.post(url, json=payload)
        logger.info(f"Message sent, status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")