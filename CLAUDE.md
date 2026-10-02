# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LPL AI Assistant is a Retrieval-Augmented Generation (RAG) application for searching company documents built for an AWS hackathon. The system uses AWS Bedrock (Claude 3.5 Sonnet + Titan Embeddings) and OpenSearch Serverless for semantic search.

## Architecture

**RAG Pipeline:**
1. Documents → Parse & Chunk (rag_engine.py:DocumentChunker)
2. Chunks → Embed via Titan (rag_engine.py:BedrockClient.embed)
3. Store in OpenSearch vector index (rag_engine.py:OpenSearchClient)
4. User Query → Embed → Vector Search → Retrieve top-k chunks
5. Chunks + Query → Claude 3.5 → Synthesized answer with citations

**Key Files:**
- `rag_engine.py` - Core RAG implementation (all-in-one for hackathon speed)
- `app.py` - Streamlit web interface
- `infra/cloudformation.yaml` - AWS infrastructure as code
- `infra/setup.sh` - Deployment script

## Development Commands

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env
# Edit .env with AWS config

# Deploy infrastructure
cd infra && ./setup.sh

# Ingest documents
python rag_engine.py ingest data/sample-docs/*.pdf

# Query from CLI
python rag_engine.py query "What is the expense policy?"

# Run web app
streamlit run app.py

# Run on specific port
streamlit run app.py --server.port 8080
```

## Configuration

All config in `rag_engine.py:Config` class:
- `BEDROCK_MODEL` - Claude model ID
- `BEDROCK_EMBEDDING_MODEL` - Titan embeddings
- `OPENSEARCH_ENDPOINT` - Set after CloudFormation deployment
- `CHUNK_SIZE` / `CHUNK_OVERLAP` - Document chunking params
- `TOP_K_RESULTS` - Number of chunks to retrieve
- `SYSTEM_PROMPT` - LLM instructions for citations

Update `.env` or modify Config class directly for hackathon speed.

## AWS Services

**Bedrock:**
- Model: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- Embeddings: `amazon.titan-embed-text-v2:0`
- Requires: Model access enabled in Bedrock console

**OpenSearch Serverless:**
- Collection type: VECTORSEARCH
- Index: k-NN with HNSW, cosine similarity
- Dimension: 1024 (Titan embedding size)

**S3:**
- Document storage (optional, can ingest from local files)

## Code Structure

`rag_engine.py` contains everything:
- `Config` - Settings
- `DocumentChunker` - PDF parsing (supports PyPDF2)
- `BedrockClient` - Embeddings & LLM generation
- `OpenSearchClient` - Vector index & search
- `RAGEngine` - Orchestrates full pipeline

Single-file design for hackathon velocity. Split into modules later if needed.

## Common Tasks

**Add support for new document type:**
1. Add parser method to `DocumentChunker` (e.g., `parse_docx`)
2. Update `ingest_documents` to handle new file extension

**Change chunking strategy:**
1. Modify `DocumentChunker.chunk_text` method
2. Adjust `Config.CHUNK_SIZE` / `CHUNK_OVERLAP`
3. Re-ingest documents

**Improve citation format:**
1. Update `Config.SYSTEM_PROMPT` with new instructions
2. Modify context formatting in `BedrockClient.generate`

**Add conversation history:**
1. Update `app.py` to pass previous messages to RAG
2. Modify `BedrockClient.generate` to accept message history
3. Update Bedrock API call with full conversation

## Testing

```bash
# Test document parsing
python -c "from rag_engine import DocumentChunker; c = DocumentChunker(); print(c.parse_pdf('test.pdf'))"

# Test embedding generation
python -c "from rag_engine import BedrockClient; b = BedrockClient(); print(len(b.embed('test')))"

# Test OpenSearch connection
python -c "from rag_engine import OpenSearchClient; o = OpenSearchClient(); o.create_index()"
```

## Troubleshooting

**"No module named 'opensearchpy'":**
- Run: `pip install -r requirements.txt`

**"Could not connect to OpenSearch":**
- Check `OPENSEARCH_ENDPOINT` in Config is correct
- Verify AWS credentials: `aws sts get-caller-identity`
- Check network policy allows public access

**"Bedrock AccessDeniedException":**
- Enable model access in AWS Console → Bedrock → Model Access
- Check IAM permissions include `bedrock:InvokeModel`

**"No space left on device" (Cloud Shell):**
- Use `/tmp` directory: `cd /tmp && git clone ...`
- Clean up: `rm -rf ~/.npm-global ~/.cache`

## Hackathon Tips

1. **Test with mock data first** - Use a few small PDFs before ingesting large corpus
2. **Hardcode config** - Modify `Config` class directly rather than .env for speed
3. **Monitor costs** - CloudWatch → Bedrock usage. ~$0.003/query with Claude Sonnet
4. **Prepare demo queries** - Curate 5-10 impressive questions that show system capabilities
5. **Citation validation** - Test that all [Source: X, p.Y] references are accurate

## Demo Script

1. Show document ingestion: `python rag_engine.py ingest sample.pdf`
2. Launch app: `streamlit run app.py`
3. Ask prepared questions that show:
   - Multi-document synthesis
   - Accurate citations
   - Handling of complex queries
4. Show source snippets in UI expander
5. Highlight: sub-5 second response time

## Post-Hackathon TODO

- [ ] Split rag_engine.py into modules
- [ ] Add authentication (Cognito)
- [ ] Implement conversation memory
- [ ] Add document upload UI
- [ ] Support DOCX, Excel, images
- [ ] Hybrid search (keyword + semantic)
- [ ] Re-ranking layer
- [ ] Query analytics dashboard
- [ ] Unit tests
- [ ] Production deployment (ECS/Lambda)
