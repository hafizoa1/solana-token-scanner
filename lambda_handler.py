import json
import logging
import traceback

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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