import os
import time
from typing import Dict, Any

from app.core.policy_manager import PolicyManager
from app.core.dispatcher import ActionDispatcher
from app.services.llm_client import LLMClient
from app.services.rag_pipeline import RAGPipeline
from app.guards.cost.semantic_cache import SemanticCache
from app.guards.cost.tracker import CostTracker
from app.guards.responsibility.pii_scrubber import PIIScrubber
from app.guards.performance.nli_checker import NLIChecker

class ControlPlaneEngine:
    def __init__(self, config_path: str = "app/config.yaml"):
        self.policy_manager = PolicyManager(config_path=config_path)
        self.llm_client = LLMClient()
        self.cache = SemanticCache(threshold=0.92)
        self.tracker = CostTracker()
        self.pii_scrubber = PIIScrubber()
        self.nli_checker = NLIChecker()
        self.rag_pipeline = RAGPipeline()
        self._initialize_knowledge_bases()

    def _initialize_knowledge_bases(self):
        """Pre-loads scenario documents into the RAG vector store if present."""
        data_paths = [
            "data/scenario_a_support/ecommerce_faq.txt",
            "data/scenario_b_internal/employee_handbook.md",
        ]
        for path in data_paths:
            if os.path.exists(path):
                self.rag_pipeline.load_document(path)

    async def process_request(self, prompt: str, scenario: str = "scenario_a_support") -> Dict[str, Any]:
        start_time = time.perf_counter()
        policy = self.policy_manager.get_policy(scenario)
        model_name = policy.get("model", "llama-3.1-8b-instant")

        # Step 1: Ingress PII Scrubbing on User Prompt
        scrubbed_prompt, prompt_has_pii, _ = self.pii_scrubber.scrub(prompt)

        # Step 2: Semantic Cache Lookup
        cached_result = self.cache.lookup(scrubbed_prompt)
        if cached_result:
            self.tracker.record_cache_hit()
            total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "action": "PASS",
                "response": cached_result["response"],
                "source": "SEMANTIC_CACHE",
                "latency_ms": total_time_ms,
                "tokens_used": 0,
                "metrics": self.tracker.get_metrics(),
                "audit": {"similarity_score": cached_result["similarity_score"]}
            }

        # Step 3: Context Retrieval via RAG Pipeline
        context = self.rag_pipeline.retrieve_context(scrubbed_prompt, top_k=2)

        # Step 4: Upstream LLM Generation
        llm_output = await self.llm_client.call_model(model_name, scrubbed_prompt, context)
        raw_response = llm_output["text"]
        self.tracker.record_llm_usage(llm_output["total_tokens"])

        # Step 5: Egress Guard Evaluations
        scrubbed_response, resp_has_pii, _ = self.pii_scrubber.scrub(raw_response)
        has_pii = prompt_has_pii or resp_has_pii

        entailment_score = self.nli_checker.verify_grounding(context, raw_response)
        
        # Simple ambiguity heuristic for financial forward-looking terms
        is_ambiguous = any(term in prompt.lower() for term in ["will", "projected", "forecast", "predict"]) and scenario == "scenario_c_finance"

        # Step 6: Dynamic Action Dispatcher Resolution
        action, final_text, audit_log = ActionDispatcher.resolve_action(
            scenario_policy=policy,
            pii_detected=has_pii,
            scrubbed_text=scrubbed_response,
            raw_text=raw_response,
            entailment_score=entailment_score,
            is_ambiguous=is_ambiguous
        )

        # Step 7: Store Valid Responses in Semantic Cache
        if action in ["PASS", "EDIT"]:
            self.cache.store(scrubbed_prompt, final_text)

        total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "action": action,
            "response": final_text,
            "source": f"LLM_{model_name.upper()}",
            "latency_ms": total_time_ms,
            "model_latency_ms": llm_output["latency_ms"],
            "tokens_used": llm_output["total_tokens"],
            "metrics": self.tracker.get_metrics(),
            "audit": audit_log
        }