"""
LPL AI Assistant - Complete RAG Engine
Single-file implementation for rapid hackathon development
"""
import json
import boto3
from typing import List, Dict, Any
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    # AWS Settings
    AWS_REGION = "us-east-1"
    BEDROCK_MODEL = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    BEDROCK_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
    
    # OpenSearch Settings (update after deployment)
    OPENSEARCH_ENDPOINT = "your-endpoint.us-east-1.aoss.amazonaws.com"
    OPENSEARCH_INDEX = "documents"
    
    # RAG Settings
    CHUNK_SIZE = 512  # tokens
    CHUNK_OVERLAP = 128
    TOP_K_RESULTS = 8
    
    # Prompts
    SYSTEM_PROMPT = """You are an AI assistant for LPL Financial employees.
Answer questions using ONLY the provided context from company documents.
Always cite sources using format: [Source: filename, p.X]
If information isn't available, clearly state that."""


# ============================================================================
# DOCUMENT CHUNKER
# ============================================================================

class DocumentChunker:
    """Parse and chunk documents"""
    
    def chunk_text(self, text: str, chunk_size: int = 512) -> List[str]:
        """Simple text chunking by character count"""
        chars_per_chunk = chunk_size * 4  # ~4 chars per token
        overlap = Config.CHUNK_OVERLAP * 4
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chars_per_chunk
            
            # Break at sentence if possible
            if end < len(text):
                period = text.rfind('. ', start, end)
                if period > start:
                    end = period + 1
            
            chunks.append(text[start:end].strip())
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    def parse_pdf(self, file_path: str) -> List[Dict]:
        """Parse PDF and return chunks with metadata"""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            
            all_chunks = []
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                chunks = self.chunk_text(text)
                
                for i, chunk in enumerate(chunks):
                    all_chunks.append({
                        'text': chunk,
                        'source_file': Path(file_path).name,
                        'page_number': page_num,
                        'chunk_index': i
                    })
            
            return all_chunks
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return []


# ============================================================================
# BEDROCK LLM CLIENT
# ============================================================================

class BedrockClient:
    """AWS Bedrock client for embeddings and LLM"""
    
    def __init__(self):
        self.client = boto3.client('bedrock-runtime', region_name=Config.AWS_REGION)
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding vector"""
        body = json.dumps({"inputText": text})
        response = self.client.invoke_model(
            modelId=Config.BEDROCK_EMBEDDING_MODEL,
            body=body
        )
        result = json.loads(response['body'].read())
        return result['embedding']
    
    def generate(self, question: str, context: List[Dict]) -> str:
        """Generate answer with citations"""
        # Format context
        context_text = "\n\n".join([
            f"[Doc {i+1}] Source: {c['source_file']}, Page: {c['page_number']}\n{c['text']}"
            for i, c in enumerate(context)
        ])
        
        # Build prompt
        user_prompt = f"""Context:\n{context_text}\n\nQuestion: {question}\n\nProvide answer with citations."""
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "temperature": 0.1,
            "system": Config.SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}]
        })
        
        response = self.client.invoke_model(
            modelId=Config.BEDROCK_MODEL,
            body=body
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text']


# ============================================================================
# OPENSEARCH CLIENT
# ============================================================================

class OpenSearchClient:
    """OpenSearch Serverless client for vector search"""
    
    def __init__(self):
        from opensearchpy import OpenSearch, RequestsHttpConnection
        from requests_aws4auth import AWS4Auth
        
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            Config.AWS_REGION,
            'aoss',
            session_token=credentials.token
        )
        
        self.client = OpenSearch(
            hosts=[{'host': Config.OPENSEARCH_ENDPOINT, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
        self.index_name = Config.OPENSEARCH_INDEX
    
    def create_index(self):
        """Create vector index"""
        index_body = {
            "settings": {"index": {"knn": True}},
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 1024,
                        "method": {
                            "name": "hnsw",
                            "engine": "faiss",
                            "space_type": "cosinesimil"
                        }
                    },
                    "text": {"type": "text"},
                    "source_file": {"type": "keyword"},
                    "page_number": {"type": "integer"}
                }
            }
        }
        
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(index=self.index_name, body=index_body)
            print(f"Created index: {self.index_name}")
    
    def index_documents(self, chunks: List[Dict]):
        """Bulk index documents"""
        from opensearchpy import helpers
        
        actions = [{
            '_index': self.index_name,
            '_source': chunk
        } for chunk in chunks]
        
        helpers.bulk(self.client, actions, refresh=True)
        print(f"Indexed {len(chunks)} chunks")
    
    def search(self, query_embedding: List[float], top_k: int = 8) -> List[Dict]:
        """Vector search"""
        query = {
            "size": top_k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": top_k
                    }
                }
            },
            "_source": {"excludes": ["embedding"]}
        }
        
        response = self.client.search(index=self.index_name, body=query)
        return [hit['_source'] for hit in response['hits']['hits']]


# ============================================================================
# RAG ENGINE
# ============================================================================

class RAGEngine:
    """Complete RAG pipeline"""
    
    def __init__(self):
        self.bedrock = BedrockClient()
        self.opensearch = OpenSearchClient()
        self.chunker = DocumentChunker()
    
    def ingest_documents(self, file_paths: List[str]):
        """Ingest documents into vector database"""
        print(f"Ingesting {len(file_paths)} documents...")
        
        # Ensure index exists
        self.opensearch.create_index()
        
        # Process each document
        all_chunks = []
        for file_path in file_paths:
            print(f"Processing: {file_path}")
            chunks = self.chunker.parse_pdf(file_path)
            
            # Generate embeddings
            for chunk in chunks:
                chunk['embedding'] = self.bedrock.embed(chunk['text'])
            
            all_chunks.extend(chunks)
        
        # Index to OpenSearch
        self.opensearch.index_documents(all_chunks)
        print(f"✅ Ingestion complete: {len(all_chunks)} chunks indexed")
    
    def query(self, question: str) -> Dict[str, Any]:
        """Answer question using RAG"""
        print(f"\nQuery: {question}")
        
        # 1. Embed question
        query_embedding = self.bedrock.embed(question)
        
        # 2. Vector search
        context = self.opensearch.search(query_embedding, top_k=Config.TOP_K_RESULTS)
        print(f"Retrieved {len(context)} relevant chunks")
        
        # 3. Generate answer
        answer = self.bedrock.generate(question, context)
        
        return {
            'question': question,
            'answer': answer,
            'sources': context
        }


# ============================================================================
# MAIN - Example Usage
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Initialize RAG engine
    rag = RAGEngine()
    
    # Example: Ingest documents
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        docs = sys.argv[2:]  # List of PDF paths
        rag.ingest_documents(docs)
    
    # Example: Query
    elif len(sys.argv) > 1 and sys.argv[1] == "query":
        question = " ".join(sys.argv[2:])
        result = rag.query(question)
        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nSources: {len(result['sources'])} documents")
    
    else:
        print("""
LPL AI Assistant - RAG Engine

Usage:
  python rag_engine.py ingest file1.pdf file2.pdf ...
  python rag_engine.py query "What is the expense policy?"
        """)
