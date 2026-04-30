import faiss
import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer

class Retriever:
    def __init__(self, db_dir="data"):
        print("Loading SentenceTransformer model...")
        self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')
        
        index_path = os.path.join(db_dir, "vector_index.faiss")
        meta_path = os.path.join(db_dir, "chunks_metadata.json")
        
        print(f"Loading FAISS index from {index_path}...")
        self.index = faiss.read_index(index_path)
        
        print(f"Loading chunks metadata from {meta_path}...")
        with open(meta_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
            
    def retrieve(self, query, top_k=5):
        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for idx in indices[0]:
            if idx < len(self.chunks):
                results.append(self.chunks[idx])
                
        return results

    def get_standard_content(self, standard_id):
        # Find the full content for a given standard_id
        for chunk in self.chunks:
            if chunk['standard_id'] == standard_id:
                return chunk['content']
        return ""
