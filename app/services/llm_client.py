import os
import time
from groq import AsyncGroq
from google import genai
from dotenv import load_dotenv


load_dotenv()

class LLMClient:
    def __init__(self):
        # Initialize the Groq client
        groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_client = AsyncGroq(api_key=groq_api_key) if groq_api_key else None
        
        # Initialize the Google GenAI client
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_client = genai.Client(api_key=gemini_api_key) if gemini_api_key else None

    async def call_model(self, model_name: str, prompt: str, context: str = "") -> dict:
        """
        Dispatches the request to the appropriate free-tier provider based on the model name.
        """
        start_time = time.perf_counter()

        if model_name.startswith("llama-"):
            result = await self._call_groq(model_name, prompt, context)
        elif model_name.startswith("gemini-"):
            result = self._call_gemini(model_name, prompt, context)
        else:
            raise ValueError(f"Unsupported model provider for {model_name}")

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        result["latency_ms"] = round(elapsed_ms, 2)
        result["model_used"] = model_name

        return result

    async def _call_groq(self, model: str, prompt: str, context: str) -> dict:
        if not self.groq_client:
            raise ValueError("GROQ_API_KEY is not set in your .env file.")
            
        system_content = "You are a helpful enterprise assistant."
        if context:
            system_content += f"\n\nContext:\n{context}"

        response = await self.groq_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        return {
            "text": response.choices[0].message.content,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }

    def _call_gemini(self, model: str, prompt: str, context: str) -> dict:
        if not self.gemini_client:
            raise ValueError("GEMINI_API_KEY is not set in your .env file.")
            
        system_instructions = "You are a helpful enterprise assistant."
        full_prompt = prompt
        
        if context:
            full_prompt = f"System Instructions: {system_instructions}\n\nContext: {context}\n\nUser Question: {prompt}"

        # Execute standard generation via Google's new GenAI SDK
        response = self.gemini_client.models.generate_content(
            model=model,
            contents=full_prompt,
        )
        
        # Safely extract token usage metadata if available
        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        comp_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
        total_tokens = getattr(usage, "total_token_count", 0) if usage else 0

        return {
            "text": response.text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": comp_tokens,
            "total_tokens": total_tokens
        }