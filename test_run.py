import os
import asyncio
from dotenv import load_dotenv

# The override=True forces Python to ignore cached terminal variables and strictly read your .env file
load_dotenv(override=True)

# Debug check: Print the first 8 characters of the key to prove it's loaded correctly
api_key = os.getenv("GROQ_API_KEY")
if api_key:
    print(f"\nDEBUG: Key found! It starts with: {api_key[:8]}...")
else:
    print("\nDEBUG: NO KEY FOUND! Python sees nothing.")

# Now import the services
from app.services.rag_pipeline import rag_pipeline
from app.services.llm_client import llm_client

async def run_test():
    # ... (Keep the rest of your run_test() code exactly the same)
    print("\n=== TEST 1: Checking the Memory (RAG Pipeline) ===")
    test_question = "What is the company policy?"
    
    print("Searching for documents...")
    context = await rag_pipeline.retrieve_context(test_question)
    print(f"Found Context:\n{context}\n")

    print("=== TEST 2: Checking the AI Stream (LLM Client) ===")
    print("AI Response: ", end="")
    
    stream = llm_client.generate_stream(prompt=test_question, context=context)
    
    async for chunk in stream:
        print(chunk, end="", flush=True)
    
    print("\n\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(run_test())