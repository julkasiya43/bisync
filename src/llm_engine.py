from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import re

class LLMEngine:
    def __init__(self, model_id="google/flan-t5-small"):
        print(f"Loading LLM: {model_id}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
        
    def extract_standards(self, query, retrieved_chunks):
        # Format the prompt
        context = ""
        for i, chunk in enumerate(retrieved_chunks):
            # Include the standard ID explicitly in the context to help the LLM extract it
            context += f"Option {i+1}: Standard ID: {chunk['standard_id']}. Content: {chunk['content'][:150]}...\n"
            
        prompt = f"""
You are a Bureau of Indian Standards (BIS) recommendation expert.
Based on the following options, identify the standard IDs that best match the query.
Return the standard IDs as a comma-separated list.

Query: {query}
Options:
{context}
Relevant Standard IDs:"""

        # Generate response
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs, max_new_tokens=50)
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Parse the output to extract standard IDs
        # Look for "IS XXX: YYYY" patterns in the output
        extracted_ids = re.findall(r'(IS\s+\d+(?:\s*\(Part\s*\d+\))?\s*:\s*\d{4})', generated_text, re.IGNORECASE)
        
        # If the LLM output is poorly formatted or didn't extract properly, 
        # fallback to the top 5 retrieved standard IDs. This ensures robustness.
        if not extracted_ids:
            # Fallback to pure retrieval result
            extracted_ids = [chunk['standard_id'] for chunk in retrieved_chunks[:5]]
            
        # Deduplicate and clean
        final_standards = []
        for std in extracted_ids:
            clean_std = re.sub(r'\s+', ' ', std).strip()
            if clean_std not in final_standards:
                final_standards.append(clean_std)
                
        # Ensure we return top 3-5
        if len(final_standards) < 3:
            # Append from retrieval if missing
            for chunk in retrieved_chunks:
                if chunk['standard_id'] not in final_standards:
                    final_standards.append(chunk['standard_id'])
                if len(final_standards) >= 5:
                    break
                    
        return final_standards[:5]

    def answer_question(self, standard_id, context, question):
        prompt = f"""
You are a Bureau of Indian Standards (BIS) compliance assistant.
Answer the user's question based strictly on the provided standard context.
If the context does not contain the answer, say "I don't have enough information to answer that."

Standard ID: {standard_id}
Context: {context[:1500]} 

Question: {question}
Answer:"""

        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs, max_new_tokens=150)
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return generated_text.strip()
