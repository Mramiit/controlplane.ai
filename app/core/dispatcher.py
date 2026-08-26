#This file takes the raw scores from your guard modules and applies your YAML policy rules to determine the final gateway action (PASS, EDIT, BLOCK, or ESCALATE).

class ActionDispatcher:
    @staticmethod
    def resolve_action(policy: dict, has_pii: bool, nli_scores: dict | None) -> dict:
        """
        Translates multi-vector threat scores into a definitive routing action.
        """
        action = "PASS"
        reason = "All enterprise safety and performance checks passed."

        # 1. Evaluate PII / Data Leak Risk
        if has_pii:
            pii_policy = policy.get("pii_action", "BLOCK")
            if pii_policy == "BLOCK":
                return {"action": "BLOCK", "reason": "Data leak detected: Request blocked by strict zero-tolerance policy."}
            elif pii_policy == "EDIT":
                action = "EDIT"
                reason = "PII detected and redacted inline."

        # 2. Evaluate Factual Grounding (Hallucination)
        if nli_scores:
            # A threshold of 0.95 means we want 95% confidence. 
            # Therefore, we flag if the contradiction probability is greater than 5% (0.05).
            confidence_needed = policy.get("hallucination_threshold", 0.90)
            max_allowed_contradiction = 1.0 - confidence_needed
            
            contra_prob = nli_scores.get("contradiction", 0.0)

            if contra_prob > max_allowed_contradiction:
                ambiguity_action = policy.get("ambiguity_action", "BLOCK")
                if ambiguity_action == "BLOCK":
                    return {
                        "action": "BLOCK",
                        "reason": f"Hallucination intercepted. Contradiction score ({contra_prob:.2f}) exceeded policy limit."
                    }
                elif ambiguity_action == "ESCALATE":
                    return {
                        "action": "ESCALATE",
                        "reason": f"Fact-checking ambiguity (Score: {contra_prob:.2f}). Escrowed to Human Review Queue."
                    }

        return {"action": action, "reason": reason}