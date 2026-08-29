"""
File: app/guards/performance/nli_checker.py
Project: ControlPlane.ai Prototype
Contributors: Rahul and Amit

Description:
Simulates a Natural Language Inference (NLI) cross-encoder. 
Evaluates the generated response against the trusted RAG context 
to detect and flag "confidently wrong" hallucinations.
"""

class NLIVerifier:
    def __init__(self, strict_threshold: float = 0.90):
        self.threshold = strict_threshold

    def verify_entailment(self, response: str, context: str) -> dict:
        """
        Calculates an entailment score. 
        In production, this runs through DeBERTa-v3-small.
        """
        response_lower = response.lower()
        context_lower = context.lower()

        # Prototype Logic: Check if the AI invented numbers not in the context
        invented_numbers = any(char.isdigit() for char in response_lower) and not any(char.isdigit() for char in context_lower)
        
        # Simulate a Contradiction (Hallucination)
        if invented_numbers or "unlimited" in response_lower or "guaranteed" in response_lower:
            return {
                "is_hallucination": True,
                "confidence_score": 0.35, # Low entailment
                "reason": "Contradiction detected against RAG context."
            }
            
        # Simulate Entailment (Factual)
        return {
            "is_hallucination": False,
            "confidence_score": 0.98, # High entailment
            "reason": "Entails context."
        }