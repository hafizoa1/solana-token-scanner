# update.sh - Script for updating existing Lambda function
#!/bin/bash

FUNCTION_NAME="token-scanner-bot"

echo "Creating updated deployment package..."
mkdir -p deployment
cd deployment

# Install dependencies
pip install -r ../requirements.txt --target .

# Copy application files
cp -r ../app .
cp ../lambda_handler.py .

# Create ZIP
zip -r ../function.zip .
cd ..

echo "Updating Lambda function..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://function.zip

echo "Update complete!"