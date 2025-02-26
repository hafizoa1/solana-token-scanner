import json
import logging
import traceback
import base64
import os
import requests
import asyncio
from app.data.fetcher import DexScreenerFetcher
from app.classifiers.simple_rule_classifier import SimpleRuleClassifier
from app.bot.telegram_bot import TokenBot

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')  # For scheduled events

def lambda_handler(event, context):
    try:
        logger.info(f"Lambda function invoked")
        
        # Check if this is a scheduled event from CloudWatch
        is_scheduled_event = 'source' in event and (
            event['source'] == 'aws.events' or 
            'detail-type' in event and event['detail-type'] == 'Scheduled Event'
        )
        
        if is_scheduled_event:
            logger.info("Processing scheduled event")
            
            if not TELEGRAM_CHAT_ID:
                logger.error("TELEGRAM_CHAT_ID environment variable not set for scheduled events")
                return {'statusCode': 500, 'body': json.dumps({"error": "TELEGRAM_CHAT_ID not set"})}
            
            # Send initial message
            send_telegram_message(TELEGRAM_CHAT_ID, "🕒 Running scheduled token scan...")
            
            # Run the scan with the default chat ID
            asyncio.run(handle_scan_directly(TELEGRAM_CHAT_ID))
            
            return {'statusCode': 200, 'body': json.dumps({"message": "Scheduled scan completed"})}
        
        # If not a scheduled event, process as a webhook from Telegram
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
            
            # Process the scan command
            asyncio.run(handle_scan_directly(chat_id))
        
        return {'statusCode': 200, 'body': json.dumps({"status": "success"})}
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}

async def handle_scan_directly(chat_id):
    """Handle the scan by running the token fetch and classification directly"""
    try:
        # Create a token bot instance with the chat_id
        bot = TokenBot(TELEGRAM_BOT_TOKEN, chat_id)
        
        # Get the fetcher and classifier
        fetcher = DexScreenerFetcher()
        classifier = SimpleRuleClassifier()
        
        try:
            # Get tokens from fetcher
            raw_tokens = await fetcher.get_validated_tokens()
            
            if not raw_tokens:
                await bot.send_message("No tokens found.")
                return True
                
            # Apply classifier
            filtered_tokens = classifier.classify(raw_tokens)
            
            if not filtered_tokens:
                await bot.send_message("No matches found.")
                return True
                
            # Format and send results in batches
            message_batches = []
            current_batch = []
            
            for i, token in enumerate(filtered_tokens, 1):
                base_token = token.get('baseToken', {})
                token_info = (
                    f"{i}. {base_token.get('symbol', 'Unknown')} ({base_token.get('name', 'Unknown')})\n"
                    f"💰 Price: ${float(token.get('priceUsd', 0)):.4f}\n"
                    f"📈 24h Vol: ${float(token.get('volume', {}).get('h24', 0)):,.0f}\n"
                    f"💧 Liq: ${float(token.get('liquidity', {}).get('usd', 0)):,.0f}\n"
                    f"📊 24h: {float(token.get('priceChange', {}).get('h24', 0)):+.1f}%\n\n"
                )
                
                current_batch.append(token_info)
                
                if len(current_batch) == 10:
                    batch_message = ''.join(current_batch)
                    message_batches.append(batch_message)
                    current_batch = []
                    
            if current_batch:
                batch_message = ''.join(current_batch)
                message_batches.append(batch_message)
                
            # Send each batch
            for batch in message_batches:
                await bot.send_message(batch)
                await asyncio.sleep(0.5)
                
            # Send completion message
            await bot.send_message(f"✅ Found {len(filtered_tokens)} tokens.")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in scan operation: {e}")
            await bot.send_message(f"❌ Error: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error handling scan: {str(e)}")
        logger.error(traceback.format_exc())
        send_telegram_message(chat_id, f"❌ Error: {str(e)}")
        return False

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