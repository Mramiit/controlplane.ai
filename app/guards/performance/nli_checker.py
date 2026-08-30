import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class NLIChecker:
    def __init__(self, model_name: str = "cross-encoder/nli-deberta-v3-small"):
        # Small, fast cross-encoder (~140MB)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()

    def verify_grounding(self, context: str, response: str) -> float:
        """
        Calculates the entailment probability (0.0 to 1.0) of the response given the context.
        Higher score = More factually grounded in the context.
        """
        if not context or not response:
            return 1.0  # Pass if no grounding context was provided

        # Cross-encoder takes pair: (Premise/Context, Hypothesis/Response)
        inputs = self.tokenizer(
            context,
            response,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            # Model outputs 3 classes: [Contradiction, Entailment, Neutral]
            probs = torch.softmax(logits, dim=-1)[0]
            
            # Index 1 corresponds to Entailment
            entailment_score = float(probs[1])

        return round(entailment_score, 4)