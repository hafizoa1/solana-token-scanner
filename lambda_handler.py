import json
import os
import logging
from app.bot.telegram_bot import TokenBot

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda entry point - handles Telegram webhook events
    
    Args:
        event (dict): AWS Lambda event object
        context (object): AWS Lambda context object
    
    Returns:
        dict: Response with status code and body
    """
    try:
        # Log the entire event for debugging
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Validate environment variables
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        if not token or not chat_id:
            logger.error("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Missing required environment variables',
                    'details': 'TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set'
                })
            }
        
        # Instantiate bot
        try:
            bot = TokenBot(token, chat_id)
        except Exception as bot_init_error:
            logger.error(f"Failed to initialize bot: {str(bot_init_error)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Bot initialization failed',
                    'details': str(bot_init_error)
                })
            }
        
        # Safely extract and parse body
        body = event.get('body', '{}')
        
        # Ensure body is a string before parsing
        if not isinstance(body, (str, bytes, bytearray)):
            body = json.dumps(body)
        
        # Parse the body
        try:
            parsed_body = json.loads(body)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse body: {body}")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid JSON in request body',
                    'received_body': str(body)
                })
            }
        
        # Extract message details
        message = parsed_body.get('message', {})
        message_text = message.get('text', '').strip()
        
        logger.info(f"Received message: {message_text}")
        
        # Handle specific commands
        if message_text == "/scan":
            try:
                response = bot.scan_command(None, None)  # Process /scan command
                logger.info("Scan command processed successfully")
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'success',
                        'message': 'Scan initiated',
                        'response': response
                    })
                }
            except Exception as scan_error:
                logger.error(f"Error processing scan command: {str(scan_error)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': 'Failed to process scan command',
                        'details': str(scan_error)
                    })
                }
        
        # Handle other scenarios or default response
        logger.info("Webhook received without specific action")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'received',
                'message': 'Webhook processed',
                'command': message_text
            })
        }
    
    except Exception as e:
        # Catch-all error handling
        logger.error(f"Unexpected error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Unexpected internal error',
                'details': str(e)
            })
        }
