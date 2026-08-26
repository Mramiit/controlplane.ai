#most important file in the prototype. It wires Phase 1 (LLM/Services) and Phase 2 (Guards) together into a single, high-speed execution pipeline.

import time
from app.core.policy_manager import PolicyManager
from app.core.dispatcher import ActionDispatcher
from app.guards.responsibility.pii_scrubber import PIIScrubber
from app.guards.cost.semantic_cache import SemanticCache
from app.guards.performance.nli_checker import LocalNLIChecker
from app.services.llm_client import LLMClient

class ControlPlaneEngine:
    def __init__(self):
        # Load Policies & Services
        self.policy_manager = PolicyManager()
        self.llm_client = LLMClient()
        
        # Load the 3 Guard Pillars
        self.pii_guard = PIIScrubber()
        self.cache_guard = SemanticCache()
        self.nli_guard = LocalNLIChecker()
        
        # Memory queue for Scenario C (Finance) escalations
        self.human_review_queue = []

    def execute(self, prompt: str, context: str = "", scenario_key: str = "scenario_a_support") -> dict:
        start_time = time.time()
        policy = self.policy_manager.get_policy(scenario_key)
        
        telemetry = {
            "scenario_applied": scenario_key, 
            "cache_hit": False, 
            "cost_saved_usd": 0.0,
            "target_model": policy.get("model")
        }

        # ── [INGRESS] STEP 1: PII Masking & Semantic Cache ──
        sanitized_prompt, pii_entities, ingress_has_pii = self.pii_guard.scan_and_redact(prompt)
        telemetry["pii_entities"] = [e["type"] for e in pii_entities]

        if policy.get("pii_action") == "BLOCK" and ingress_has_pii:
            return self._format_response("BLOCK", "Ingress blocked: PII detected in prompt.", start_time, telemetry)

        if policy.get("semantic_cache_enabled", False):
            cached_res, sim_score = self.cache_guard.lookup(
                sanitized_prompt, policy.get("similarity_threshold", 0.92)
            )
            if cached_res:
                telemetry["cache_hit"] = True
                telemetry["cost_saved_usd"] = 0.002 # Estimated saved compute
                return self._format_response("PASS (CACHE)", cached_res, start_time, telemetry)

        # ── [GENERATION] STEP 2: Upstream LLM Call ──
        raw_response, token_usage = self.llm_client.generate(sanitized_prompt, context, scenario_key)
        telemetry["token_usage"] = token_usage

        # ── [EGRESS] STEP 3: Hallucination & Leak Checks ──
        sanitized_response, egress_entities, egress_has_pii = self.pii_guard.scan_and_redact(raw_response)
        
        nli_scores = None
        if context:
            nli_scores = self.nli_guard.check_grounding(context, sanitized_response)
            telemetry["nli_contradiction_score"] = round(nli_scores["contradiction"], 3)

        # ── [DISPATCH] STEP 4: Action Matrix ──
        decision = ActionDispatcher.resolve_action(
            policy=policy, 
            has_pii=(ingress_has_pii or egress_has_pii), 
            nli_scores=nli_scores
        )

        final_text = sanitized_response
        if decision["action"] == "BLOCK":
            final_text = f"[BLOCKED] Output terminated: {decision['reason']}"
        elif decision["action"] == "ESCALATE":
            self.human_review_queue.append({"prompt": sanitized_prompt, "response": raw_response, "scores": nli_scores})
            final_text = f"[FLAGGED FOR REVIEW] {sanitized_response}"
        elif decision["action"] in ["PASS", "EDIT"]:
            if policy.get("semantic_cache_enabled", False):
                self.cache_guard.store(sanitized_prompt, final_text)

        telemetry["dispatch_reason"] = decision["reason"]
        return self._format_response(decision["action"], final_text, start_time, telemetry)

    def _format_response(self, action: str, text: str, start_time: float, telemetry: dict) -> dict:
        total_time_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "action": action,
            "latency_ms": total_time_ms,
            "response": text,
            "telemetry": telemetry
        }