```mermaid
graph TD
    %% Entry Points
    User[👤 Telegram User] -->|Sends "scan"| API_Gateway
    CronJob[⏳ AWS EventBridge] --> API_Gateway

    %% API Gateway to Lambda
    API_Gateway[🌐 API Gateway] -->|Trigger| Lambda_Function

    %% Data Flow
    Lambda_Function -->|Fetch Trending Tokens| DexScreener[🔍 DexScreener API]
    Lambda_Function -->|Fetch Additional Data| Jupiter[🚀 Jupiter API]

    %% Service Components
    Lambda_Function -->|Process Tokens| TokenService[📊 Token Service]
    TokenService -->|Classify Tokens| Classifier[🧠 Token Classifier]

    %% Classification Outcomes
    Classifier -->|Categorize| Moonshots[🚀 Moonshots]
    Classifier -->|Categorize| Stable[💼 Stable Tokens]
    Classifier -->|Categorize| Risky[⚠️ Risky Tokens]

    %% Response Mechanism
    Lambda_Function -->|Send Notification| TelegramBot[🤖 Telegram Bot]
    TelegramBot -->|Deliver Results| User

    %% CI/CD and Deployment
    GitHubActions[🔄 GitHub Actions] -->|Deploy| S3
    S3[📦 AWS S3] -->|Update| Lambda_Function

    %% Monitoring
    Lambda_Function -->|Log Events| CloudWatch[📋 CloudWatch]
```
