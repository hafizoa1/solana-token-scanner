import json
import logging
import traceback
import os
import requests

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get Telegram bot token from environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

def lambda_handler(event, context):
    try:
        # Log the entire event with maximum detail
        logger.info("Raw Event Type: %s", type(event))
        logger.info("Raw Event Keys: %s", list(event.keys()) if event else "No keys (event is None)")
        
        # Attempt to log the full event as JSON
        try:
            logger.info("Full Event JSON: %s", json.dumps(event, indent=2))
        except Exception as json_error:
            logger.error(f"Could not convert event to JSON: {str(json_error)}")
        
        # Check if event is None
        if event is None:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Received None event',
                    'message': 'Event payload is empty or improperly formatted'
                })
            }
        
        # Defensive parsing
        body = event.get('body', event)
        
        # If body is a string, try to parse it
        if isinstance(body, str):
            try:
                parsed_body = json.loads(body)
            except json.JSONDecodeError:
                parsed_body = body
        else:
            parsed_body = body
        
        logger.info("Parsed Body Type: %s", type(parsed_body))
        logger.info("Parsed Body: %s", parsed_body)
        
        # Handle Telegram message
        if isinstance(parsed_body, dict) and 'message' in parsed_body:
            process_telegram_message(parsed_body)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'message': 'Event received and processed',
                'event_type': str(type(event)),
                'body_type': str(type(parsed_body))
            })
        }
    
    except Exception as e:
        # Comprehensive error logging
        logger.error("Unexpected error: %s", str(e))
        logger.error("Traceback: %s", traceback.format_exc())
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Unexpected internal error',
                'details': str(e),
                'traceback': traceback.format_exc()
            })
        }

def process_telegram_message(update):
    """Process incoming Telegram message"""
    # Extract message data
    message = update.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', '')
    
    logger.info(f"Processing message: '{text}' from chat_id: {chat_id}")
    
    # Check if this is a /scan command
    if text and text.startswith('/scan'):
        # Extract any parameters after the /scan command
        params = text.replace('/scan', '').strip()
        
        # Here is where you would call your scan function
        # For now, we'll just return a placeholder response
        response_text = f"Scanning token: {params}" if params else "Please provide a token address to scan"
        
        # Send response back to user
        send_telegram_reply(chat_id, response_text)
    else:
        logger.info("Message is not a scan command, ignoring")

def send_telegram_reply(chat_id, text):
    """Send a reply back to the Telegram user"""
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
        response.raise_for_status()
        logger.info(f"Message sent successfully: {response.json()}")
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        logger.error(traceback.format_exc())