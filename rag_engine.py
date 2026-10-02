"""
LPL AI Assistant - Complete RAG Engine
Single-file implementation for rapid hackathon development
"""
import json
import os
import pickle
import boto3
import numpy as np
import faiss
from typing import List, Dict, Any, Optional
from pathlib import Path


# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
    BEDROCK_MODEL = os.environ.get(
        "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    )
    BEDROCK_EMBEDDING_MODEL = os.environ.get(
        "BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0"
    )
    EMBEDDING_DIMENSION = 1024

    # OpenSearch (optional — set endpoint to use instead of FAISS)
    OPENSEARCH_ENDPOINT = os.environ.get("OPENSEARCH_ENDPOINT", "")
    OPENSEARCH_INDEX = os.environ.get("OPENSEARCH_INDEX_NAME", "documents")

    # FAISS local store path
    FAISS_DIR = os.environ.get(
        "FAISS_DIR", str(Path(__file__).parent / "vector_store")
    )

    # RAG settings
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 128
    TOP_K_RESULTS = 8

    SYSTEM_PROMPT = """You are an AI assistant for LPL Financial employees.
Answer questions using ONLY the provided context from company documents.
Always cite sources using format: [Source: filename, p.X]
If information isn't available, clearly state that."""

    @classmethod
    def use_opensearch(cls) -> bool:
        return bool(cls.OPENSEARCH_ENDPOINT) and "your-endpoint" not in cls.OPENSEARCH_ENDPOINT


# ============================================================================
# DOCUMENT CHUNKER
# ============================================================================

class DocumentChunker:
    def chunk_text(self, text: str, chunk_size: int = 512) -> List[str]:
        chars_per_chunk = chunk_size * 4
        overlap = Config.CHUNK_OVERLAP * 4
        chunks = []
        start = 0
        while start < len(text):
            end = start + chars_per_chunk
            if end < len(text):
                period = text.rfind('. ', start, end)
                if period > start:
                    end = period + 1
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap if end < len(text) else end
        return chunks

    def parse_pdf(self, file_path: str) -> List[Dict]:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            all_chunks = []
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if not text:
                    continue
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
            print(f"Error parsing {file_path}: {e}")
            return []

    def parse_text(self, file_path: str) -> List[Dict]:
        try:
            text = Path(file_path).read_text()
            chunks = self.chunk_text(text)
            return [
                {
                    'text': chunk,
                    'source_file': Path(file_path).name,
                    'page_number': 1,
                    'chunk_index': i
                }
                for i, chunk in enumerate(chunks)
            ]
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []

    def parse_file(self, file_path: str) -> List[Dict]:
        ext = Path(file_path).suffix.lower()
        if ext == '.pdf':
            return self.parse_pdf(file_path)
        elif ext in ('.txt', '.md', '.csv'):
            return self.parse_text(file_path)
        else:
            print(f"Unsupported file type: {ext}")
            return []


# ============================================================================
# BEDROCK LLM CLIENT
# ============================================================================

class BedrockClient:
    def __init__(self):
        self.client = boto3.client('bedrock-runtime', region_name=Config.AWS_REGION)

    def embed(self, text: str) -> List[float]:
        body = json.dumps({"inputText": text})
        response = self.client.invoke_model(
            modelId=Config.BEDROCK_EMBEDDING_MODEL,
            body=body
        )
        result = json.loads(response['body'].read())
        return result['embedding']

    def generate(self, question: str, context: List[Dict]) -> str:
        context_text = "\n\n".join([
            f"[Doc {i+1}] Source: {c['source_file']}, Page: {c['page_number']}\n{c['text']}"
            for i, c in enumerate(context)
        ])
        user_prompt = f"Context:\n{context_text}\n\nQuestion: {question}\n\nProvide answer with citations."

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
# FAISS LOCAL VECTOR STORE
# ============================================================================

class FAISSClient:
    def __init__(self):
        self.store_dir = Path(Config.FAISS_DIR)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.store_dir / "index.faiss"
        self.meta_path = self.store_dir / "metadata.pkl"
        self.index: Optional[faiss.IndexFlatIP] = None
        self.metadata: List[Dict] = []
        self._load()

    def _load(self):
        if self.index_path.exists() and self.meta_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.meta_path, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            self.index = faiss.IndexFlatIP(Config.EMBEDDING_DIMENSION)
            self.metadata = []

    def _save(self):
        faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, 'wb') as f:
            pickle.dump(self.metadata, f)

    def create_index(self):
        pass

    def index_documents(self, chunks: List[Dict]):
        vectors = []
        for chunk in chunks:
            vec = np.array(chunk['embedding'], dtype='float32')
            vec /= np.linalg.norm(vec)
            vectors.append(vec)

            meta = {k: v for k, v in chunk.items() if k != 'embedding'}
            self.metadata.append(meta)

        if vectors:
            matrix = np.stack(vectors)
            self.index.add(matrix)
            self._save()
            print(f"Indexed {len(vectors)} chunks (total: {self.index.ntotal})")

    def search(self, query_embedding: List[float], top_k: int = 8) -> List[Dict]:
        if self.index.ntotal == 0:
            return []

        vec = np.array([query_embedding], dtype='float32')
        vec /= np.linalg.norm(vec)
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.metadata):
                result = dict(self.metadata[idx])
                result['score'] = float(score)
                results.append(result)
        return results


# ============================================================================
# OPENSEARCH CLIENT
# ============================================================================

class OpenSearchClient:
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
        index_body = {
            "settings": {"index": {"knn": True}},
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": Config.EMBEDDING_DIMENSION,
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
        from opensearchpy import helpers
        actions = [{'_index': self.index_name, '_source': chunk} for chunk in chunks]
        helpers.bulk(self.client, actions, refresh=True)
        print(f"Indexed {len(chunks)} chunks")

    def search(self, query_embedding: List[float], top_k: int = 8) -> List[Dict]:
        query = {
            "size": top_k,
            "query": {"knn": {"embedding": {"vector": query_embedding, "k": top_k}}},
            "_source": {"excludes": ["embedding"]}
        }
        response = self.client.search(index=self.index_name, body=query)
        return [hit['_source'] for hit in response['hits']['hits']]


# ============================================================================
# RAG ENGINE
# ============================================================================

class RAGEngine:
    def __init__(self):
        self.bedrock = BedrockClient()
        self.chunker = DocumentChunker()
        if Config.use_opensearch():
            print("Using OpenSearch Serverless backend")
            self.vector_store = OpenSearchClient()
        else:
            print("Using FAISS local backend")
            self.vector_store = FAISSClient()

    def ingest_documents(self, file_paths: List[str]):
        print(f"Ingesting {len(file_paths)} documents...")
        self.vector_store.create_index()

        all_chunks = []
        for file_path in file_paths:
            print(f"Processing: {file_path}")
            chunks = self.chunker.parse_file(file_path)
            print(f"  {len(chunks)} chunks extracted")

            for j, chunk in enumerate(chunks):
                chunk['embedding'] = self.bedrock.embed(chunk['text'])
                if (j + 1) % 10 == 0:
                    print(f"  Embedded {j + 1}/{len(chunks)} chunks")

            all_chunks.extend(chunks)

        self.vector_store.index_documents(all_chunks)
        print(f"Ingestion complete: {len(all_chunks)} chunks indexed")

    def query(self, question: str) -> Dict[str, Any]:
        query_embedding = self.bedrock.embed(question)
        context = self.vector_store.search(query_embedding, top_k=Config.TOP_K_RESULTS)

        if not context:
            return {
                'question': question,
                'answer': "No documents have been ingested yet. Please ingest documents first.",
                'sources': []
            }

        answer = self.bedrock.generate(question, context)
        return {
            'question': question,
            'answer': answer,
            'sources': context
        }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("""
LPL AI Assistant - RAG Engine

Usage:
  python rag_engine.py ingest file1.pdf file2.pdf ...
  python rag_engine.py query "What is the expense policy?"
  python rag_engine.py status
        """)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "ingest":
        if len(sys.argv) < 3:
            print("Usage: python rag_engine.py ingest <file1> [file2] ...")
            sys.exit(1)
        import glob
        files = []
        for pattern in sys.argv[2:]:
            files.extend(glob.glob(pattern))
        if not files:
            print("No files found matching the given paths.")
            sys.exit(1)
        rag = RAGEngine()
        rag.ingest_documents(files)

    elif cmd == "query":
        if len(sys.argv) < 3:
            print("Usage: python rag_engine.py query \"your question\"")
            sys.exit(1)
        question = " ".join(sys.argv[2:])
        rag = RAGEngine()
        result = rag.query(question)
        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nSources: {len(result['sources'])} documents referenced")

    elif cmd == "status":
        store_dir = Path(Config.FAISS_DIR)
        if Config.use_opensearch():
            print(f"Backend: OpenSearch ({Config.OPENSEARCH_ENDPOINT})")
        elif (store_dir / "index.faiss").exists():
            idx = faiss.read_index(str(store_dir / "index.faiss"))
            print(f"Backend: FAISS (local)")
            print(f"Vectors indexed: {idx.ntotal}")
            print(f"Store path: {store_dir}")
        else:
            print("Backend: FAISS (local) - no documents ingested yet")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
