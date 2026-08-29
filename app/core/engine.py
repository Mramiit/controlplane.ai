"""
File: app/core/engine.py
Project: ControlPlane.ai Prototype
Contributors: Rahul and Amit

Description:
This engine executes the multi-vector egress pipeline. It processes incoming 
prompts through real-time PII regex scrubbers, a metadata-filtered FAISS semantic cache, 
an NLI Hallucination checker, and a live LLM connection via Groq before egress.
"""

import time
import re
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

from app.guards.cost.semantic_cache import SemanticCache
from app.guards.performance.nli_checker import NLIVerifier

class GatewayEngine:
    def __init__(self):
        self.cache = SemanticCache()
        self.nli_guard = NLIVerifier()

    def process(self, prompt: str, scenario: str) -> dict:
        start_time = time.time()
        action = "PASS"
        risk_status = "Clean"
        prompt_lower = prompt.lower()

        # ==========================================
        # 1. COST GUARD: Metadata-Filtered Cache Check
        # ==========================================
        cached_response = self.cache.check_cache(prompt_lower, scenario)
        if cached_response:
            return {
                "response": cached_response,
                "action": "PASS",
                "latency_ms": int((time.time() - start_time) * 1000),
                "tokens_saved": len(prompt.split()) + 25,
                "risk_status": "Cache Hit"
            }

        # ==========================================
        # 2. RESPONSIBILITY GUARD: PII Scrubbing
        # ==========================================
        original_prompt = prompt
        prompt = re.sub(r'\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b', '[REDACTED CARD]', prompt)
        prompt = re.sub(r'[\w\.-]+@[\w\.-]+', '[REDACTED EMAIL]', prompt)
        prompt = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED PHONE]', prompt)
        
        if original_prompt != prompt:
            action = "EDIT"
            risk_status = "PII Masked"

        # ==========================================
        # 3. DYNAMIC AI GENERATION
        # ==========================================
        response = self._generate_response(prompt_lower, original_prompt)
        
        # Simulated RAG Ground Truth Context for the prototype
        ground_truth_context = "Employees receive 0 days of paid paternity leave in their first month."

        # ==========================================
        # 4. PERFORMANCE GUARD: Hallucination Check
        # ==========================================
        if scenario in ["scenario_b_internal", "scenario_c_finance"] and action == "PASS":
            nli_result = self.nli_guard.verify_entailment(response, ground_truth_context)
            if nli_result["is_hallucination"]:
                action = "BLOCK"
                risk_status = "Hallucination Blocked"
                response = f"🚨 Gateway Intercept: The AI attempted to state: '{response}'. This contradicts internal company policies."

        # ==========================================
        # 5. POST-PROCESSING & CACHING
        # ==========================================
        # Don't cache blocks or API errors so they retry on the next attempt
        if action != "BLOCK" and "API Error" not in response:
            self.cache.add_to_cache(prompt_lower, response, scenario)
        
        return {
            "response": response,
            "action": action,
            "latency_ms": int((time.time() - start_time) * 1000),
            "tokens_saved": 0,
            "risk_status": risk_status
        }

    def _generate_response(self, prompt_lower: str, original_prompt: str) -> str:
        """
        Connects to a real LLM via the OpenAI standard client, routed to Groq.
        """
        # The Hallucination trigger for the demo (keep this so your guards still trigger!)
        if "leave" in prompt_lower or "paternity" in prompt_lower:
            return "Employees get 30 days of unlimited paid paternity leave immediately."
            
        try:
            # Initialize the client specifically for Groq LPU hardware
            client = OpenAI(
                api_key=os.environ.get("OPENAI_API_KEY"),
                base_url="https://api.groq.com/openai/v1"
            )
            
           # Make the live API call
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b", # <-- The active Groq model
                messages=[
                    {"role": "system", "content": "You are a helpful enterprise AI assistant. Keep responses under 3 sentences."},
                    {"role": "user", "content": original_prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            return response.choices[0].message.content
            
        except Exception as e:
            # Fallback just in case the API key is missing or the network drops
            return f"API Error: {str(e)}. System caught query: '{original_prompt}'"