import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import re

class LLMEngine:
    def __init__(self, model_id="Qwen/Qwen2.5-1.5B-Instruct"):
        print(f"Loading LLM: {model_id} (This may take a minute...)")
        
        # Qwen 2.5 is completely UNGATED! No HuggingFace login required!
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        
        # Load in float32 for CPU by default, or bfloat16 for modern GPUs.
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else "cpu"
        )
        
        self.pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer
        )
        
    def extract_standards(self, query, retrieved_chunks):
        # Format the context
        context = ""
        for i, chunk in enumerate(retrieved_chunks):
            context += f"Option {i+1}: Standard ID: {chunk['standard_id']}. Content: {chunk['content'][:150]}...\n"
            
        # Llama 3 uses specific chat templates for instructions
        messages = [
            {"role": "system", "content": "You are a Bureau of Indian Standards (BIS) recommendation expert. Output ONLY the comma-separated standard IDs (e.g., IS 1234 : 2020) and nothing else."},
            {"role": "user", "content": f"Based on the following options, identify the standard IDs that best match the query.\n\nQuery: {query}\nOptions:\n{context}\nRelevant Standard IDs:"}
        ]

        # Generate response
        outputs = self.pipeline(
            messages, 
            max_new_tokens=50, 
            do_sample=False,  # Keep it deterministic for extraction
            return_full_text=False # Don't return the prompt
        )
        generated_text = outputs[0]["generated_text"].strip()
        
        # Parse the output to extract standard IDs
        extracted_ids = re.findall(r'(IS\s+\d+(?:\s*\(Part\s*\d+\))?\s*:\s*\d{4})', generated_text, re.IGNORECASE)
        
        # Fallback to pure retrieval result if formatting failed
        if not extracted_ids:
            extracted_ids = [chunk['standard_id'] for chunk in retrieved_chunks[:5]]
            
        # Deduplicate and clean
        final_standards = []
        for std in extracted_ids:
            clean_std = re.sub(r'\s+', ' ', std).strip()
            if clean_std not in final_standards:
                final_standards.append(clean_std)
                
        # Ensure we return top 3-5
        if len(final_standards) < 3:
            for chunk in retrieved_chunks:
                if chunk['standard_id'] not in final_standards:
                    final_standards.append(chunk['standard_id'])
                if len(final_standards) >= 5:
                    break
                    
        return final_standards[:5]

    def answer_question(self, standard_id, context, question):
        messages = [
            {"role": "system", "content": "You are a Bureau of Indian Standards (BIS) compliance assistant. Answer the user's question based strictly on the provided standard context. Keep it concise."},
            {"role": "user", "content": f"Standard ID: {standard_id}\nContext: {context[:1500]}\n\nQuestion: {question}"}
        ]

        outputs = self.pipeline(
            messages, 
            max_new_tokens=150,
            do_sample=True,
            temperature=0.3, # Slight creativity for natural chat
            return_full_text=False
        )
        generated_text = outputs[0]["generated_text"].strip()
        return generated_text
