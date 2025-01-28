# deploy.sh - Initial deployment script
#!/bin/bash

FUNCTION_NAME="token-scanner-bot"
REGION="us-east-1"  # Change to your region

echo "Creating deployment package..."
mkdir -p deployment
cd deployment

# Install dependencies to deployment directory
pip install -r ../requirements.txt --target .

# Copy application files
cp -r ../app .
cp ../lambda_handler.py .

# Create ZIP
zip -r ../function.zip .
cd ..

echo "Creating Lambda function..."
aws lambda create-function \
    --function-name $FUNCTION_NAME \
    --runtime python3.9 \
    --handler lambda_handler.lambda_handler \
    --role $(aws iam get-role --role-name lambda-token-bot-role --query 'Role.Arn' --output text) \
    --zip-file fileb://function.zip \
    --timeout 300 \
    --memory-size 256 \
    --environment "Variables={TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN,TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID}"

echo "Setting up scheduled execution..."
aws events put-rule \
    --name "${FUNCTION_NAME}-schedule" \
    --schedule-expression "cron(0 0,12 * * ? *)"

echo "Deployment complete!"