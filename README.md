# 🤖 LPL AI Assistant

**AI-powered document search and synthesis for LPL Financial employees**

Built for the AWS Financial Services Hackathon using AWS Bedrock RAG architecture.

---

## 🎯 What It Does

Employees can ask natural language questions about company documents and receive synthesized answers with source citations:

**Example:**
> **Q:** "What is our expense reimbursement policy?"  
> **A:** "Expense reimbursement requests must be submitted within 30 days of the expense date [Source: hr_policy.pdf, p.15]. Manager approval is required for expenses over $500 [Source: finance_guide.pdf, p.8]."

---

## 🏗️ Architecture

```
User Query
    ↓
Embed via Titan
    ↓
Vector Search (OpenSearch)
    ↓
Retrieve Top-K Documents
    ↓
Claude 3.5 Sonnet Synthesis
    ↓
Answer + Citations
```

**Tech Stack:**
- **LLM:** AWS Bedrock (Claude 3.5 Sonnet)
- **Embeddings:** Titan Embeddings v2  
- **Vector DB:** Amazon OpenSearch Serverless
- **Frontend:** Streamlit
- **Storage:** Amazon S3

---

## ⚡ Quick Start (5 Minutes)

### Prerequisites
- AWS account with Bedrock access enabled
- Python 3.9+
- AWS CLI configured

### 1️⃣ Deploy AWS Infrastructure
```bash
cd infra
./setup.sh
# Wait 5-10 minutes for CloudFormation
```

### 2️⃣ Configure Environment
```bash
# Update with CloudFormation outputs
cp .env.example .env
nano .env
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Ingest Documents
```bash
# Add your PDFs to data/sample-docs/
python rag_engine.py ingest data/sample-docs/*.pdf
```

### 5️⃣ Run the App
```bash
streamlit run app.py
```

Open **http://localhost:8501** and start asking questions!

---

## 📁 Project Structure

```
lpl-ai-assistant/
├── rag_engine.py           # Core RAG implementation (all-in-one)
├── app.py                  # Streamlit web interface
├── requirements.txt        # Python dependencies
├── .env.example           # Configuration template
├── infra/
│   ├── cloudformation.yaml # AWS infrastructure
│   └── setup.sh           # Deployment script
├── data/sample-docs/      # Your PDF documents
├── QUICKSTART.md          # Detailed setup guide
└── CLAUDE.md              # Development guide for Claude Code
```

---

## 🎮 Usage

### CLI Mode
```bash
# Ingest documents
python rag_engine.py ingest file1.pdf file2.pdf file3.pdf

# Query from command line
python rag_engine.py query "What is the compliance policy?"
```

### Web Interface
```bash
streamlit run app.py
```
- Type questions in the chat interface
- View synthesized answers with inline citations
- Expand "View Sources" to see original document snippets

---

## ⚙️ Configuration

Edit `rag_engine.py` Config class:

```python
class Config:
    AWS_REGION = "us-east-1"
    BEDROCK_MODEL = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    OPENSEARCH_ENDPOINT = "your-endpoint.us-east-1.aoss.amazonaws.com"
    
    CHUNK_SIZE = 512        # Tokens per chunk
    CHUNK_OVERLAP = 128     # Overlap between chunks
    TOP_K_RESULTS = 8       # Documents to retrieve
```

---

## 💰 Cost Estimate

For typical hackathon usage (100 queries, 1000 document chunks):

- **Bedrock (Claude 3.5 Sonnet):** ~$5-8
- **Bedrock (Titan Embeddings):** ~$1-2
- **OpenSearch Serverless:** Free tier (4 OCU-hours/day)
- **S3:** <$1

**Total:** ~$10-15 for 2 days

---

## 🧪 Testing

```bash
# Test document parsing
python -c "from rag_engine import DocumentChunker; 
           c = DocumentChunker(); 
           print(c.parse_pdf('test.pdf'))"

# Test embedding generation
python -c "from rag_engine import BedrockClient; 
           b = BedrockClient(); 
           print(len(b.embed('test text')))"

# Test OpenSearch connection
python -c "from rag_engine import OpenSearchClient; 
           o = OpenSearchClient(); 
           o.create_index()"
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **ImportError: No module named 'opensearchpy'** | `pip install -r requirements.txt` |
| **Could not connect to OpenSearch** | Check `OPENSEARCH_ENDPOINT` in rag_engine.py matches CloudFormation output |
| **Bedrock AccessDeniedException** | Enable model access in AWS Console → Bedrock → Model access |
| **No space left on device (Cloud Shell)** | Clone to `/tmp`: `cd /tmp && git clone ...` |

**Check AWS credentials:**
```bash
aws sts get-caller-identity
```

---

## 🎯 Demo Strategy

1. **Prep data:** Curate 10-15 realistic LPL documents (policies, guides, FAQs)
2. **Ingest:** Run ingestion pipeline before demo
3. **Prepare queries:** Write 5-7 impressive questions that show:
   - Multi-document synthesis
   - Accurate citations
   - Complex reasoning
4. **Live demo:** 
   - Show Streamlit interface
   - Ask prepared questions
   - Highlight sub-5 second responses
   - Open "View Sources" to show citations
5. **Wow factor:** Ask a question that requires synthesizing 3+ documents

---

## 🚀 Post-Hackathon Roadmap

- [ ] Split `rag_engine.py` into modular architecture
- [ ] Add authentication (AWS Cognito)
- [ ] Implement conversation memory
- [ ] Document upload UI
- [ ] Support DOCX, Excel, images in PDFs
- [ ] Hybrid search (keyword + semantic)
- [ ] Re-ranking layer (Cohere, Bedrock)
- [ ] Query analytics dashboard
- [ ] Production deployment (ECS Fargate)
- [ ] Unit & integration tests

---

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Detailed setup instructions
- **[CLAUDE.md](CLAUDE.md)** - Developer guide for Claude Code
- **[AWS Bedrock Docs](https://docs.aws.amazon.com/bedrock/)** - API reference

---

## 👥 Team

Built for the AWS Financial Services Hackathon by [Your Team Name]

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🆘 Support

For issues during the hackathon:
- Check troubleshooting section above
- Review CloudFormation stack events in AWS Console
- Check CloudWatch logs for Bedrock API calls

**AWS Support:** [AWS Support Center](https://console.aws.amazon.com/support/)
