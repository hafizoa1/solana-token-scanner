import os
import json
import logging
import traceback
import base64
import requests
import asyncio
from app.bot.telegram_bot import TokenBot
from app.data.fetcher import DexScreenerFetcher
from app.classifiers.enhanced_meme_token_classifier import EnhancedMemeTokenClassifier
from app.services.token_service import TokenService
import app.config as config

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', config.BOT_TOKEN_PROD)
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', config.CHAT_ID_PROD)

def lambda_handler(event, context):
    """
    AWS Lambda handler that processes both scheduled CloudWatch events and Telegram webhook events.
    """
    try:
        logger.info("Lambda function invoked")
        
        # Check if this is a scheduled CloudWatch event
        if is_scheduled_event(event):
            logger.info("Processing scheduled event")
            if not TELEGRAM_CHAT_ID:
                logger.error("TELEGRAM_CHAT_ID environment variable not set for scheduled events")
                return {'statusCode': 500, 'body': json.dumps({"error": "TELEGRAM_CHAT_ID not set"})}
                
            send_telegram_message(TELEGRAM_CHAT_ID, "🕒 Running scheduled token scan...")
            run_scan(TELEGRAM_CHAT_ID)
            return {'statusCode': 200, 'body': json.dumps({"message": "Scheduled scan completed"})}
        
        # Otherwise, handle Telegram webhook events
        body = extract_request_body(event)
        if not body:
            return {'statusCode': 400, 'body': json.dumps({"error": "No body in request"})}
            
        telegram_update = json.loads(body)
        message = telegram_update.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        
        logger.info(f"Message: '{text}', Chat ID: {chat_id}")
        
        if text and text.startswith('/scan'):
            logger.info("Detected /scan command")
            send_telegram_message(chat_id, "🔍 Starting scan...")
            run_scan(chat_id)
        
        return {'statusCode': 200, 'body': json.dumps({"status": "success"})}
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}

def is_scheduled_event(event):
    """Detects if the incoming event is a scheduled CloudWatch trigger."""
    return 'source' in event and event['source'] == 'aws.events'

def extract_request_body(event):
    """Extracts and decodes the request body if necessary."""
    body = event.get('body')
    if event.get('isBase64Encoded', False) and body:
        return base64.b64decode(body).decode('utf-8')
    return body

def create_service():
    """Creates and initializes the token service with dependencies."""
    # Create dependencies
    fetcher = DexScreenerFetcher()
    
    # Create classifier
    classifier = EnhancedMemeTokenClassifier()
    
    # Create service with dependencies
    return TokenService(fetcher, classifier)

def run_scan(chat_id):
    """Runs the token scan and sends results to the specified chat."""
    try:
        # Create a dummy Update and Context for scan_command
        from telegram import Update
        
        # Initialize service
        token_service = create_service()
        
        # Initialize the bot with token service
        bot = TokenBot(TELEGRAM_BOT_TOKEN, chat_id, token_service)
        
        # Create a minimal Update object
        update = Update.de_json(
            {
                'update_id': 0,
                'message': {
                    'message_id': 0,
                    'date': 0,
                    'chat': {
                        'id': chat_id,
                        'type': 'private',
                        'first_name': 'User',
                        'username': 'user'
                    },
                    'text': '/scan',
                    'from': {
                        'id': chat_id,
                        'is_bot': False,
                        'first_name': 'User',
                        'username': 'user'
                    }
                }
            },
            bot.application.bot
        )
        
        # Run the scan_command with the dummy Update object
        asyncio.run(bot.scan_command(update, None))
        logger.info("Scan completed successfully")
        
        # Clean up resources
        asyncio.run(token_service.shutdown())
        
    except Exception as e:
        logger.error(f"Error in scan operation: {e}")
        logger.error(traceback.format_exc())
        send_telegram_message(chat_id, f"❌ Error: {str(e)}")

def send_telegram_message(chat_id, text):
    """Sends a message via Telegram API."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    
    try:
        response = requests.post(url, json=payload)
        logger.info(f"Message sent, status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")