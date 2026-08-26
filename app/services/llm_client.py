# File: app/services/llm_client.py
# Purpose: Scaffolds the upstream model connections to stream text asynchronously. 
# Solves the latency bottleneck by enabling Speculative Streaming Verification.
# Author/Completed by: Rahul - Implemented the async generator wrapper using Groq's async client to yield chunks.

import os
from groq import AsyncGroq

class LLMClient:
    def __init__(self):
        # We use the AsyncGroq client for maximum streaming speed
        self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    # FIX: Updated to an authorized model explicitly listed on your Groq tier
    async def generate_stream(self, prompt: str, context: str, model: str = "qwen/qwen3.8-27b"):
        """
        Sends the prompt and context to the AI and streams the response back token-by-token.
        """
        system_message = (
            "You are a helpful enterprise assistant. "
            "Use the following retrieved context to answer the user's question. "
            "If the answer is not in the context, do not guess. "
            f"\n\nContext:\n{context}"
        )

        try:
            # stream=True is the most critical flag for real-time evaluation
            stream = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )

            # Yield each token chunk exactly as it arrives from the model
            async for chunk in stream:
                token = chunk.choices[0].delta.content
                if token:
                    yield token

        except Exception as e:
            yield f"[Error generating response: {str(e)}]"

# Global instance to be imported by the orchestration engine
llm_client = LLMClient()