# 🔧 AWS Account Setup

## Prerequisites

Before running the application, you need to enable AWS Bedrock model access.

## Step 1: Enable Bedrock Model Access

### 1. Open AWS Bedrock Console
```
https://console.aws.amazon.com/bedrock/
```

### 2. Navigate to Model Access
- In the left sidebar, click **"Model access"**
- Or go directly: https://console.aws.amazon.com/bedrock/home#/modelaccess

### 3. Request Model Access
Click **"Manage model access"** or **"Edit"**

**Enable these models:**
- ✅ **Claude 3.5 Sonnet v2** (anthropic.claude-3-5-sonnet-20241022-v2:0)
- ✅ **Titan Embeddings G1 - Text v2** (amazon.titan-embed-text-v2:0)

Optional (for experimentation):
- Claude 3 Haiku (faster, cheaper alternative)
- Claude 3 Opus (most capable, slower)

### 4. Submit Request
- Check the boxes for the models
- Click **"Request model access"** or **"Save changes"**
- Wait 1-2 minutes for approval (usually instant)

### 5. Verify Access
- Status should show **"Access granted"** with a green checkmark
- If pending, wait a few minutes and refresh

## Step 2: Configure AWS CLI

### Check Current Configuration
```bash
aws sts get-caller-identity
```

Should return your AWS account ID, user ARN, etc.

### If Not Configured
```bash
aws configure
```

Enter:
- AWS Access Key ID
- AWS Secret Access Key  
- Default region: `us-east-1` (recommended for Bedrock)
- Output format: `json`

### Test Bedrock Access
```bash
# List available models
aws bedrock list-foundation-models --region us-east-1

# Test Claude invocation
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --region us-east-1 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}' \
  /tmp/response.json

cat /tmp/response.json
```

## Step 3: IAM Permissions

Your AWS user/role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "aoss:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*"
      ],
      "Resource": "*"
    }
  ]
}
```

For hackathon purposes, you can use an admin user with **AdministratorAccess**.

## Step 4: Region Considerations

**Recommended Region: us-east-1 (N. Virginia)**

Claude 3.5 Sonnet is available in:
- us-east-1 (N. Virginia)
- us-west-2 (Oregon)
- eu-west-1 (Ireland)
- ap-southeast-1 (Singapore)
- ap-northeast-1 (Tokyo)

Update `rag_engine.py` Config if using a different region:
```python
AWS_REGION = "us-east-1"
BEDROCK_REGION = "us-east-1"
```

## Troubleshooting

### "AccessDeniedException: User is not authorized"
→ Enable model access in Bedrock console (Step 1)

### "ValidationException: The provided model identifier is invalid"
→ Check model ID matches exactly:
```
anthropic.claude-3-5-sonnet-20241022-v2:0
```

### "ThrottlingException: Rate exceeded"
→ Bedrock has usage quotas. For hackathon, request quota increase:
- Console: Service Quotas → AWS Bedrock
- Or continue after cooldown period

### "ServiceQuotaExceededException"
→ Request quota increase in Service Quotas console

## Cost Management

### Set Billing Alert
1. Go to AWS Billing Dashboard
2. Set up a billing alarm (e.g., $50 threshold)
3. You'll receive email if costs exceed threshold

### Monitor Usage
```bash
# Check Bedrock usage (CloudWatch)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name Invocations \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-12-31T23:59:59Z \
  --period 86400 \
  --statistics Sum
```

### Cost Estimates
- Claude 3.5 Sonnet: $3 per million input tokens, $15 per million output tokens
- Titan Embeddings: $0.10 per million tokens
- OpenSearch Serverless: $0.24/OCU-hour (free tier: 4 OCU-hours/day)

**Hackathon estimate:** $10-15 total for 100 queries

## Ready to Deploy!

Once AWS is configured:
```bash
cd infra
./setup.sh
```

Then follow QUICKSTART.md to complete setup.
