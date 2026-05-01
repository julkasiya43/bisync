from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import time
import os
import sys

# Ensure the root directory is in sys.path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retriever import Retriever
from src.llm_engine import LLMEngine

app = FastAPI(title="BIS Standards Recommendation Engine")

# Initialize models
print("Initializing RAG models for API...")
retriever = Retriever(db_dir="data")
llm_engine = LLMEngine()
print("Initialization complete.")

class QueryRequest(BaseModel):
    query: str

class RecommendationResponse(BaseModel):
    standards: list
    latency_seconds: float
    context: list

class ChatRequest(BaseModel):
    standard_id: str
    question: str

class ChatResponse(BaseModel):
    answer: str
    latency_seconds: float

@app.post("/api/recommend", response_model=RecommendationResponse)
def recommend_standards(req: QueryRequest):
    start_time = time.time()
    
    # 1. Retrieve
    retrieved_chunks = retriever.retrieve(req.query, top_k=5)
    
    # 2. Extract
    extracted_standards = llm_engine.extract_standards(req.query, retrieved_chunks)
    
    latency = round(time.time() - start_time, 2)
    
    # Also pass context snippets to frontend for beautiful display
    context_snippets = []
    for chunk in retrieved_chunks:
        if chunk['standard_id'] in extracted_standards:
            context_snippets.append({
                "id": chunk['standard_id'],
                "snippet": chunk['content'][:150] + "..."
            })
            
    # Add any missing standards that were extracted but not in context directly (shouldn't happen, but fallback)
    extracted_set = set([c['id'] for c in context_snippets])
    for std in extracted_standards:
        if std not in extracted_set:
             context_snippets.append({
                "id": std,
                "snippet": "Detailed description available in standard documentation."
             })
             
    return RecommendationResponse(
        standards=extracted_standards,
        latency_seconds=latency,
        context=context_snippets[:5] # limit to 5
    )

@app.post("/api/chat", response_model=ChatResponse)
def chat_with_standard(req: ChatRequest):
    start_time = time.time()
    
    # Get the context for the requested standard
    context = retriever.get_standard_content(req.standard_id)
    if not context:
        return ChatResponse(answer="Sorry, I couldn't find the detailed documentation for this standard.", latency_seconds=0)
        
    answer = llm_engine.answer_question(req.standard_id, context, req.question)
    
    latency = round(time.time() - start_time, 2)
    return ChatResponse(answer=answer, latency_seconds=latency)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
    
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8056)
