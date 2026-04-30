# BIS Standards Recommendation Engine

This is a Retrieval-Augmented Generation (RAG) prototype built for the BIS Standards Recommendation Engine Hackathon. It identifies relevant Bureau of Indian Standards (BIS) regulations based on product descriptions, specifically focusing on Building Materials.

## Project Structure
- `src/ingest.py`: Parses the `dataset.pdf`, extracts standard numbers and text, chunks the documents, and generates embeddings using `BAAI/bge-small-en-v1.5`. Stores them in FAISS vector DB.
- `src/retriever.py`: Loads the FAISS index and handles top-K vector search for a given product query.
- `src/llm_engine.py`: Loads `google/flan-t5-small` locally for generating/extracting standard IDs from retrieved context, acting as the RAG generation step.
- `inference.py`: The entry-point script for automated testing by judges.
- `eval_script.py`: The official evaluation script.
- `data/`: Contains the FAISS index and chunks metadata.

## Setup Instructions
1. Install Python 3.9+ (if not already installed).
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the ingestion pipeline (ensure `dataset.pdf` is in the correct path):
   ```bash
   python src/ingest.py
   ```

## Running the Web UI (Frontend)
We built a premium, aesthetic pastel-themed web interface for the recommendation engine. To start the API server and UI:
```bash
python src/api.py
```
Then, open your browser and navigate to `http://localhost:8056`.

### Key UI Features
- **"Talk to Standard" Chat:** Click the chat button on any recommended standard to ask specific compliance questions. The AI will stream the answer in real-time.
- **Voice Search:** Use the microphone icon to verbally describe your product instead of typing.
- **Smart Highlighting:** Keywords from your query are dynamically highlighted in the standard snippets.
- **3D Magnetic Hover:** Results cards tilt towards your mouse cursor with an aesthetic 3D effect.

## Running Inference
The system is fully runnable on consumer hardware (CPU is supported). To run inference on a test set:
```bash
python inference.py --input "public_test_set.json" --output "team_results.json"
```

## Running Evaluation
Calculate the automated metrics using:
```bash
python eval_script.py --results team_results.json
```

## System Architecture & Strategy
- **Chunking Strategy**: A precise text-extraction method that uses Regex (`SUMMARY OF IS...`) to group each standard and its summary into one contiguous chunk.
- **Retrieval Strategy**: Utilizes `BAAI/bge-small-en-v1.5` dense embeddings mapped into a FAISS L2 index for extremely fast nearest-neighbor retrieval.
- **LLM Pipeline**: We use `google/flan-t5-small` alongside rule-based fallbacks to ensure `< 5 seconds` latency while extracting the correct `IS XXXX : YYYY` format strictly. No external APIs are used to maintain complete data privacy.
