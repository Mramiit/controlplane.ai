from typing import Dict, Any, Tuple

class ActionDispatcher:
    @staticmethod
    def resolve_action(
        scenario_policy: Dict[str, Any],
        pii_detected: bool,
        scrubbed_text: str,
        raw_text: str,
        entailment_score: float,
        is_ambiguous: bool = False
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Determines the dynamic governance action: PASS, EDIT, ESCALATE, or BLOCK.
        Returns: (action, final_text, audit_metadata)
        """
        pii_policy = scenario_policy.get("pii_action", "BLOCK")
        hallucination_thresh = scenario_policy.get("hallucination_threshold", 0.90)
        ambiguity_policy = scenario_policy.get("ambiguity_action", "PASS")

        audit_log = {
            "pii_detected": pii_detected,
            "entailment_score": entailment_score,
            "hallucination_threshold": hallucination_thresh,
            "is_ambiguous": is_ambiguous
        }

        # 1. PII Governance Check
        if pii_detected:
            if pii_policy == "BLOCK":
                audit_log["reason"] = "Blocked: Sensitive PII detected under strict policy."
                return "BLOCK", "[REQUEST BLOCKED BY CONTROLPLANE: SENSITIVE DATA DETECTED]", audit_log
            elif pii_policy == "EDIT":
                final_text = scrubbed_text
                audit_log["action_applied"] = "Inline PII redaction applied."
            else:
                final_text = raw_text
        else:
            final_text = raw_text

        # 2. Hallucination / Grounding Check
        if entailment_score < hallucination_thresh:
            if scenario_policy.get("ambiguity_action") == "BLOCK":
                audit_log["reason"] = f"Blocked: Factual grounding score ({entailment_score}) below threshold ({hallucination_thresh})."
                return "BLOCK", "[REQUEST BLOCKED BY CONTROLPLANE: FACTUAL CONTRADICTION DETECTED]", audit_log
            elif scenario_policy.get("ambiguity_action") == "ESCALATE":
                audit_log["reason"] = f"Escalated: Factual grounding score ({entailment_score}) requires human review."
                return "ESCALATE", f"[FLAGGED FOR HUMAN REVIEW]\n{final_text}", audit_log

        # 3. Ambiguity & Uncertainty Escalation Check
        if is_ambiguous and ambiguity_policy == "ESCALATE":
            audit_log["reason"] = "Escalated: High forward-looking ambiguity detected."
            return "ESCALATE", f"[AUDIT QUEUE ESCALATION]\n{final_text}", audit_log

        # 4. Default Action (Pass or Edit)
        action = "EDIT" if pii_detected and pii_policy == "EDIT" else "PASS"
        return action, final_text, audit_log