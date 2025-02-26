import os
import json
import logging
import traceback
import base64
import requests
import asyncio
from app.bot.telegram_bot import TokenBot

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')  # Default chat ID for scheduled scans

def lambda_handler(event, context):
    """
    AWS Lambda handler that processes both scheduled CloudWatch events and Telegram webhook events.
    """
    try:
        logger.info(f"Lambda function invoked")

        # Check if this is a scheduled CloudWatch event
        if _is_scheduled_event(event):
            logger.info("Processing scheduled event")
            return _handle_scheduled_event()

        # Otherwise, handle Telegram webhook events
        return _handle_telegram_event(event)
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}

def _is_scheduled_event(event):
    """Detects if the incoming event is a scheduled CloudWatch trigger."""
    return 'source' in event and event['source'] == 'aws.events'

def _handle_scheduled_event():
    """Handles scheduled scans by using the default chat ID."""
    if not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_CHAT_ID environment variable not set for scheduled events")
        return {'statusCode': 500, 'body': json.dumps({"error": "TELEGRAM_CHAT_ID not set"})}

    send_telegram_message(TELEGRAM_CHAT_ID, "🕒 Running scheduled token scan...")
    bot = TokenBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    asyncio.run(bot.scan_command())
    return {'statusCode': 200, 'body': json.dumps({"message": "Scheduled scan completed"})}

def _handle_telegram_event(event):
    """Processes Telegram bot messages received via Lambda webhook."""
    body = _extract_request_body(event)
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
        bot = TokenBot(TELEGRAM_BOT_TOKEN, chat_id)
        asyncio.run(bot.scan_command())
    
    return {'statusCode': 200, 'body': json.dumps({"status": "success"})}

def _extract_request_body(event):
    """Extracts and decodes the request body if necessary."""
    body = event.get('body')
    if event.get('isBase64Encoded', False) and body:
        return base64.b64decode(body).decode('utf-8')
    return body

def send_telegram_message(chat_id, text):
    """Sends a message via Telegram API."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    
    try:
        response = requests.post(url, json=payload)
        logger.info(f"Message sent, status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
