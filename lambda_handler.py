import os
import json
import logging
import base64
import requests
import asyncio
import traceback

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def lambda_handler(event, context):
    """
    AWS Lambda handler that processes GitHub deployment tests, 
    scheduled CloudWatch events, and Telegram webhook events.
    """
    try:
        logger.info(f"Lambda function invoked with event: {json.dumps(event)}")
        
        # Handle GitHub deployment test
        if event.get('source') == 'github-action-test':
            logger.info("Processing GitHub deployment test")
            return {
                'statusCode': 200,
                'body': json.dumps({"message": "Deployment test successful"})
            }
        
        # Check if this is a scheduled CloudWatch event
        if 'source' in event and event['source'] == 'aws.events':
            logger.info("Processing scheduled event")
            
            # Only attempt to send messages if TELEGRAM_CHAT_ID is set
            if not TELEGRAM_CHAT_ID:
                logger.error("TELEGRAM_CHAT_ID environment variable not set for scheduled events")
                return {'statusCode': 500, 'body': json.dumps({"error": "TELEGRAM_CHAT_ID not set"})}
                
            send_telegram_message(TELEGRAM_CHAT_ID, "🕒 Running scheduled token scan...")
            
            # Simple response for now - we'll implement the actual scan later
            return {'statusCode': 200, 'body': json.dumps({"message": "Scheduled scan completed"})}
        
        # Handle Telegram webhook events
        body = None
        if 'body' in event:
            body = event['body']
            if event.get('isBase64Encoded', False) and body:
                body = base64.b64decode(body).decode('utf-8')
        
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
            
            # Simple response for now - we'll implement the actual scan later
            return {'statusCode': 200, 'body': json.dumps({"status": "success"})}
        
        return {'statusCode': 200, 'body': json.dumps({"status": "success"})}
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}

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