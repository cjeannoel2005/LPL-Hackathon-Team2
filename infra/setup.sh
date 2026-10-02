#!/bin/bash
# Quick setup script for AWS infrastructure

STACK_NAME="lpl-ai-assistant"
REGION="${AWS_REGION:-us-east-1}"

echo "🚀 Deploying LPL AI Assistant Infrastructure..."
echo "Region: $REGION"
echo ""

# Deploy CloudFormation
aws cloudformation create-stack \
  --stack-name $STACK_NAME \
  --template-body file://cloudformation.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

echo "⏳ Waiting for stack creation (this may take 5-10 minutes)..."
aws cloudformation wait stack-create-complete \
  --stack-name $STACK_NAME \
  --region $REGION

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Infrastructure deployed successfully!"
  echo ""
  echo "📋 Getting outputs..."
  aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs' \
    --output table
  
  echo ""
  echo "💡 Update your .env file with these values"
else
  echo "❌ Stack creation failed"
  exit 1
fi
