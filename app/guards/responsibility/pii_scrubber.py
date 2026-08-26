import re
from typing import Tuple
from presidio_analyzer import AnalyzerEngine

class PIIScrubber:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        # Custom deterministic regex patterns for credit cards and phone numbers
        self.patterns = {
            "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
            "PHONE_NUMBER": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        }

    def scrub(self, text: str) -> Tuple[str, bool, list]:
        """
        Detects sensitive entities and redacts them inline.
        Returns: (scrubbed_text, pii_detected_bool, list_of_entities_found)
        """
        detected_entities = []
        scrubbed_text = text

        # 1. Fast Regex Pass
        for entity_type, pattern in self.patterns.items():
            matches = list(re.finditer(pattern, scrubbed_text))
            if matches:
                detected_entities.append(entity_type)
                scrubbed_text = re.sub(pattern, f"[{entity_type}_REDACTED]", scrubbed_text)

        # 2. Presidio NLP Analyzer Pass (Detects Names, SSN, API Keys, etc.)
        results = self.analyzer.analyze(text=scrubbed_text, language="en")
        for res in results:
            if res.score > 0.6:
                detected_entities.append(res.entity_type)
                # Replace entity span with redaction tag
                start, end = res.start, res.end
                scrubbed_text = scrubbed_text[:start] + f"[{res.entity_type}_REDACTED]" + scrubbed_text[end:]

        has_pii = len(detected_entities) > 0
        return scrubbed_text, has_pii, list(set(detected_entities))