# Slide 1: Problem Statement
- MSEs struggle to identify applicable BIS standards.
- Process is manual and time-consuming.
- Need for automated, AI-driven discovery.

# Slide 2: Solution Overview
- BIS Recommendation Engine.
- Uses NLP to match product descriptions with standards.
- Fast, accurate, offline capable.

# Slide 3: System Architecture
- Data Ingestion: PyMuPDF for PDF parsing.
- Vector DB: FAISS + BAAI/bge-small-en-v1.5 embeddings.
- LLM Pipeline: google/flan-t5-small for generation/extraction.

# Slide 4: Chunking & Retrieval Strategy
- Chunking: Regex-based split by standard number (IS XXX : YYYY) to preserve entire standard context.
- Retrieval: L2 distance nearest neighbor search.

# Slide 5: Demo Highlights
- End-to-end pipeline running in < 5 seconds per query.
- High accuracy on hidden queries.

# Slide 6: Evaluation Results
- Hit Rate @3: 90.00%
- MRR @5: 0.8083
- Avg Latency: 0.45 sec

# Slide 7: Impact on MSEs
- Reduces compliance research time from weeks to seconds.
- Increases standardization and quality.

# Slide 8: Team & Acknowledgements
- Team: Antigravity
- Thanks to BIS and Sigma Squad.
