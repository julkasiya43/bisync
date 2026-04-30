import pymupdf
import re
import json
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def extract_and_chunk_pdf(pdf_path):
    print(f"Reading PDF from {pdf_path}...")
    doc = pymupdf.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
        
    print(f"Total text length: {len(text)}")
    
    # Split text by "SUMMARY OF" followed by "IS"
    raw_chunks = re.split(r'(?=SUMMARY OF\s+IS\s+\d+)', text, flags=re.IGNORECASE)
    
    chunks = []
    print(f"Found {len(raw_chunks)} raw sections.")
    
    for chunk in raw_chunks:
        # Check if the chunk actually starts with our pattern
        match = re.search(r'SUMMARY OF\s+(IS\s+\d+(?:\s*\([^)]+\))?\s*:\s*\d{4})', chunk, re.IGNORECASE)
        if match:
            std_id = match.group(1).strip()
            # Clean up the text: remove excess whitespace
            clean_text = re.sub(r'\s+', ' ', chunk).strip()
            # To limit the chunk size and keep it relevant, we could optionally truncate
            chunks.append({
                "standard_id": std_id,
                "content": clean_text
            })
                
    print(f"Extracted {len(chunks)} standards chunks.")
    return chunks

def build_vector_db(chunks, db_dir="data"):
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    print("Loading embedding model (BAAI/bge-small-en-v1.5)...")
    model = SentenceTransformer('BAAI/bge-small-en-v1.5')
    
    print("Generating embeddings...")
    texts = [c['content'] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    
    print("Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    faiss.write_index(index, os.path.join(db_dir, "vector_index.faiss"))
    
    with open(os.path.join(db_dir, "chunks_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
        
    print("Vector DB successfully built and saved.")

if __name__ == "__main__":
    pdf_path = "Bureau of Indian Standards x Sigma Squad AI Hackathon Materials/dataset.pdf"
    chunks = extract_and_chunk_pdf(pdf_path)
    build_vector_db(chunks)
