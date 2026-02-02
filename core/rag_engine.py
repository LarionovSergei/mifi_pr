import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import logging
import uuid
import os

try:
    from config import config
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RagEngine:
    def __init__(self):
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=config.CHROMA_PATH)
        
        # Initialize Embedding Function (using local model)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=config.EMBEDDING_MODEL
        )
        
        # Get or Create Collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="habr_articles",
            embedding_function=self.embedding_fn
        )

    def add_documents(self, documents: List[Dict]):
        """
        Adds a list of documents to the ChromaDB collection.
        Documents must have 'full_text' and metadata.
        """
        ids = []
        texts = []
        metadatas = []
        
        for doc in documents:
            # Basic chunking: taking the whole text for now or first 2000 chars to avoid limits if any
            # In a real scenario, we should use a proper chunker (RecursiveCharacterTextSplitter)
            text_content = doc.get('full_text', '')
            if not text_content:
                continue
                
            # Splitting large texts into chunks could be done here.
            # For this MVP, let's keep it simple: one article = one or a few chunks.
            # Let's simple truncate for speed if too long, or better: just store it.
            # Local models might have context limits (e.g. 512 tokens).
            # SentenceTransformer handles truncation usually.
            
            chunk_size = 1000
            for i in range(0, len(text_content), chunk_size):
                chunk = text_content[i:i+chunk_size]
                chunk_id = str(uuid.uuid4())
                
                ids.append(chunk_id)
                texts.append(chunk)
                metadatas.append({
                    "title": doc.get('title', ''),
                    "link": doc.get('link', ''),
                    "pub_date": doc.get('pub_date', ''),
                    "creator": doc.get('creator', ''),
                    "description": doc.get('description', ''),
                    "chunk_index": i // chunk_size
                })
        
        if ids:
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(ids)} chunks to the database.")

    def search(self, query: str, n_results: int = 3, filters: Dict = None) -> List[Dict]:
        """
        Searches for relevant documents using semantic search.
        Supports filtering by metadata (e.g. {'creator': 'Author Name'}).
        """
        if not query:
            return []
            
        # Prepare chroma where clause
        where_clause = {}
        if filters:
            for k, v in filters.items():
                if v: # Only add if value is present
                    where_clause[k] = v
        
        # If where_clause is empty, pass None
        where_arg = where_clause if where_clause else None

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2, # Fetch more to deduplicate
                where=where_arg
            )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
        
        unique_results = []
        seen_links = set()
        
        if results['documents']:
            docs = results['documents'][0]
            metas = results['metadatas'][0]
            
            for i in range(len(docs)):
                link = metas[i]['link']
                if link not in seen_links:
                    seen_links.add(link)
                    unique_results.append({
                        'content': docs[i],
                        'metadata': metas[i]
                    })
                    if len(unique_results) >= n_results:
                        break
        
        return unique_results

    def get_recommendations(self, article_title: str, n_results: int = 3) -> List[Dict]:
        """
        Finds articles similar to the given one.
        Excludes the article itself from results.
        """
        # Fetch more results to allow buffering for exclusion
        raw_results = self.search(article_title, n_results=n_results + 2)
        
        filtered_results = []
        for res in raw_results:
            # Simple title check to exclude self
            if res['metadata']['title'] != article_title:
                filtered_results.append(res)
            
            if len(filtered_results) >= n_results:
                break
                
        return filtered_results


if __name__ == "__main__":
    # Test script
    rag = RagEngine()
    
    # Try adding some dummy data if you want, or just search
    # rag.add_documents([{'title': 'Test', 'link': 'http://test', 'full_text': 'This is a test article about Python and AI.'}])
    
    results = rag.search("Python")
    for r in results:
        print(f"Found: {r['metadata']['title']}")
        print(f"Snippet: {r['content'][:100]}...")
