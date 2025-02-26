import json
import logging
import traceback
import base64
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
        logger.info("Raw Event Keys: %s", list(event.keys()) if isinstance(event, dict) else "Not a dict")
        
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
        
        # Extract body from the event
        body = event.get('body')
        is_base64 = event.get('isBase64Encoded', False)
        
        # If body is base64 encoded, decode it
        if is_base64 and body:
            try:
                logger.info("Decoding base64 body")
                body_bytes = base64.b64decode(body)
                body = body_bytes.decode('utf-8')
                logger.info(f"Decoded body: {body}")
            except Exception as e:
                logger.error(f"Error decoding base64 body: {str(e)}")
        
        # Parse the body as JSON
        if body:
            try:
                parsed_body = json.loads(body)
                logger.info(f"Parsed Telegram update: {json.dumps(parsed_body, indent=2)}")
                
                # Process the Telegram message
                process_telegram_message(parsed_body)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON body: {str(e)}")
                parsed_body = body
        else:
            parsed_body = event
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'message': 'Event received and processed'
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
    try:
        # Extract message data
        message = update.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        
        logger.info(f"Processing message: '{text}' from chat_id: {chat_id}")
        
        # Check if this is a /scan command
        if text and text.startswith('/scan'):
            # Extract any parameters after the /scan command
            params = text.replace('/scan', '').strip()
            logger.info(f"Scan command detected with params: '{params}'")
            
            # Here is where you would call your scan function
            # For now, we'll just return a placeholder response
            if params:
                response_text = f"Scanning token: {params}"
            else:
                response_text = "Please provide a token address to scan. Usage: /scan [token_address]"
            
            # Send response back to user
            send_telegram_reply(chat_id, response_text)
        else:
            logger.info("Message is not a scan command, ignoring")
            
            # Optional: respond to unknown commands
            # send_telegram_reply(chat_id, "I only understand /scan commands. Try '/scan [token_address]'")
    except Exception as e:
        logger.error(f"Error processing Telegram message: {str(e)}")
        logger.error(traceback.format_exc())

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
        logger.info(f"Sending response to chat_id {chat_id}: '{text}'")
        response = requests.post(url, json=payload)
        logger.info(f"Telegram API response: {response.status_code} - {response.text[:100]}")
        
        response.raise_for_status()
        logger.info("Message sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        logger.error(traceback.format_exc())
        return False