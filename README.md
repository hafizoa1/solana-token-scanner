# solana-token-scanner

graph TD;
    %% Entry Points
    User[👤 Telegram User] -->|Sends "/scan"| API_Gateway;
    CronJob[⏳ AWS EventBridge (6hr cron job)] --> API_Gateway;
    
    %% API Gateway to Lambda
    API_Gateway[🌐 API Gateway] -->|Triggers| Lambda_Function;
    
    %% Fetching Data
    Lambda_Function[⚙️ AWS Lambda (Processing)] -->|Fetch Data| Fetcher_Service;
    Fetcher_Service[📡 Fetcher Service] -->|Get Data| Jupyter_API;
    Fetcher_Service -->|Get Data| Dex_Screener_API;
    
    %% Classification
    Fetcher_Service -->|Send Processed Data| Classifier_Service;
    Classifier_Service[🧠 Classifier Service] -->|Classify Tokens| Classification[🎯 "Moonshot, Stable, Risky"];
    
    %% Response to User
    Classification -->|Return Result| Lambda_Function;
    Lambda_Function -->|Send Reply| Telegram_Bot;
    Telegram_Bot[🤖 Telegram Bot] -->|User Receives Data| User;
    
    %% Deployment and CI/CD
    GitHub_Actions[🚀 GitHub Actions] -->|Run Tests & Deploy| S3_Bucket;
    S3_Bucket[📦 AWS S3 (Stores function.zip)] -->|Lambda Pulls Code| Lambda_Function;
    
    %% Logging & Monitoring
    Lambda_Function -->|Logs| CloudWatch[📊 AWS CloudWatch];
