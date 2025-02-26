import json
import logging
import traceback
import base64
import os
import requests
import asyncio
from telegram import Bot, Update
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
            handle_result = asyncio.run(handle_scan_directly(chat_id))
            
            if handle_result:
                logger.info("Scan command processed successfully")
            else:
                logger.error("Scan command failed")
        
        return {'statusCode': 200, 'body': json.dumps({"status": "success"})}
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}

async def handle_scan_directly(chat_id):
    """Handle the scan command by running the token fetch and classification directly"""
    try:
        # We'll bypass the Update object entirely and just run the scanning logic directly
        
        # Create a token bot instance with the chat_id
        bot = TokenBot(TELEGRAM_BOT_TOKEN, chat_id)
        
        # Run the scan using TokenBot's application
        from app.data.fetcher import DexScreenerFetcher
        from app.classifiers.simple_rule_classifier import SimpleRuleClassifier
        
        # Get the fetcher and classifier that would be used in the TokenBot
        fetcher = DexScreenerFetcher()
        classifier = SimpleRuleClassifier()
        
        # This mimics the scan_command logic without needing an Update object
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