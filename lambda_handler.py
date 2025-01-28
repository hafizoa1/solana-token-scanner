import json
import os
import asyncio
from app.bot.telegram_bot import TokenBot

async def perform_bot_tasks():
    """Execute bot tasks"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        raise ValueError("Missing environment variables")
        
    bot = TokenBot(token, chat_id)
    
    try:
        await bot.send_message("🔍 Starting scheduled token scan...")
        # Assuming your TokenBot has a method to perform scan
        await bot.scan_command(None, None)  # You might need to adapt this based on your bot's implementation
        return True
    except Exception as e:
        print(f"Error in bot tasks: {str(e)}")
        return False

def lambda_handler(event, context):
    """AWS Lambda entry point"""
    try:
        # Check if this is an API Gateway event (webhook)
        if 'body' in event:
            body = json.loads(event['body'])
            # Handle webhook updates here if needed
            return {
                'statusCode': 200,
                'body': json.dumps('Webhook received')
            }
        
        # If it's a scheduled event or direct invocation
        success = asyncio.run(perform_bot_tasks())
        
        if success:
            return {
                'statusCode': 200,
                'body': json.dumps('Bot tasks completed successfully')
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps('Bot tasks failed')
            }
            
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }