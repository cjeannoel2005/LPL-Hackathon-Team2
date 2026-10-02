# Quick Start Guide (5 Minutes)

## Prerequisites
- AWS account with Bedrock access
- Python 3.9+
- AWS CLI configured

## Steps

### 1. Deploy Infrastructure (5-10 min)
```bash
cd infra
./setup.sh
# Wait for CloudFormation completion
```

### 2. Configure
```bash
# Copy outputs from CloudFormation to .env
cp .env.example .env
nano .env  # Update OPENSEARCH_ENDPOINT and S3_BUCKET_NAME
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Ingest Sample Documents
```bash
# Add PDFs to data/sample-docs/
python rag_engine.py ingest data/sample-docs/*.pdf
```

### 5. Run the App
```bash
streamlit run app.py
```

## Test Query
Open http://localhost:8501 and ask:
- "What are the key policies mentioned in the documents?"
- "Summarize the compliance requirements"

## Troubleshoot
If errors, check:
1. AWS credentials: `aws sts get-caller-identity`
2. Bedrock model access enabled in console
3. OpenSearch endpoint in .env matches CloudFormation output
