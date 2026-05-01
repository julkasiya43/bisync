import argparse
import json
import time
import os
import sys

# Ensure src modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.retriever import Retriever
from src.llm_engine import LLMEngine

def main():
    parser = argparse.ArgumentParser(description="BIS Hackathon Inference Script")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSON file")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file")
    args = parser.parse_args()

    # Load data
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    print("Initializing pipeline components...")
    retriever = Retriever(db_dir="data")
    llm_engine = LLMEngine()

    results = []
    print(f"Processing {len(data)} queries...")
    
    for item in data:
        query_id = item.get("id")
        query_text = item.get("query")
        
        start_time = time.time()
        
        # 1. Retrieve
        retrieved_chunks = retriever.retrieve(query_text, top_k=5)
        
        # 2. Generate
        extracted_standards = llm_engine.extract_standards(query_text, retrieved_chunks)
        
        end_time = time.time()
        latency = round(end_time - start_time, 2)
        
        # Format result
        result_item = {
            "id": query_id,
            "retrieved_standards": extracted_standards,
            "latency_seconds": latency
        }
        
        # Carry over other fields if present (like expected_standards for testing)
        for k, v in item.items():
            if k not in result_item:
                result_item[k] = v
                
        results.append(result_item)
        print(f"Processed {query_id} in {latency}s. Standards: {extracted_standards}")

    # Save output
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"Successfully processed {len(data)} queries. Results saved to {args.output}")

if __name__ == "__main__":
    main()
