import json
import logging
import traceback
import base64
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CallbackContext
from app.bot.telegram_bot import TokenBot

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get Telegram bot token from environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Global bot instance
bot = None

def lambda_handler(event, context):
    try:
        # Log the event
        logger.info("Raw Event Type: %s", type(event))
        try:
            logger.info("Full Event JSON: %s", json.dumps(event, indent=2))
        except Exception as json_error:
            logger.error(f"Could not convert event to JSON: {str(json_error)}")
        
        # Extract and decode body
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
        telegram_update = None
        if body:
            try:
                telegram_update = json.loads(body)
                logger.info(f"Parsed Telegram update")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON body: {str(e)}")
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid JSON payload'})
                }
        else:
            logger.error("No body found in event")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No body in request'})
            }
        
        # Convert the JSON to a Telegram Update object
        update_obj = Update.de_json(telegram_update, None)
        
        # Extract information from the update
        chat_id = None
        command = None
        
        if update_obj and update_obj.message:
            chat_id = update_obj.message.chat_id
            if update_obj.message.text:
                text = update_obj.message.text
                logger.info(f"Received message: {text}")
                if text.startswith('/scan'):
                    command = 'scan'
        
        if not chat_id:
            logger.error("Could not extract chat_id from update")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Could not extract chat_id'})
            }
        
        # Process the command
        if command == 'scan':
            # Run the scan command
            logger.info(f"Running scan command for chat_id: {chat_id}")
            # We need to run the async function in a synchronous context
            asyncio.run(process_scan_command(update_obj, chat_id))
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'message': 'Command processed successfully'
            })
        }
    
    except Exception as e:
        # Comprehensive error logging
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Unexpected internal error',
                'details': str(e),
                'traceback': traceback.format_exc()
            })
        }

async def process_scan_command(update_obj, chat_id):
    """Process the scan command asynchronously"""
    global bot
    
    try:
        if not bot:
            logger.info("Initializing TokenBot")
            # Use the chat_id from the update as the default
            bot = TokenBot(TELEGRAM_BOT_TOKEN, chat_id)
        else:
            # Update the chat_id to the current one
            bot.chat_id = chat_id
        
        # Create a minimal context
        context = None  # We don't need the context for the scan command
        
        # Call the scan command handler directly
        logger.info("Calling scan_command method")
        await bot.scan_command(update_obj, context)
        
        logger.info("Scan command processed successfully")
    except Exception as e:
        logger.error(f"Error processing scan command: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Try to send an error message
        try:
            if bot:
                await bot.send_message(f"❌ Error processing scan command: {str(e)}")
        except Exception as send_error:
            logger.error(f"Could not send error message: {str(send_error)}")