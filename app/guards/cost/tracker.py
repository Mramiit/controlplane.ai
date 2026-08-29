from typing import Dict, Any

class CostTracker:
    def __init__(self, cost_per_1k_tokens: float = 0.0015):
        # Default pricing benchmark (~$0.0015 per 1k tokens)
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.total_requests = 0
        self.cache_hits = 0
        self.tokens_consumed = 0
        self.tokens_saved = 0

    def record_llm_usage(self, total_tokens: int):
        self.total_requests += 1
        self.tokens_consumed += total_tokens

    def record_cache_hit(self, estimated_saved_tokens: int = 150):
        self.total_requests += 1
        self.cache_hits += 1
        self.tokens_saved += estimated_saved_tokens

    def get_metrics(self) -> Dict[str, Any]:
        cost_incurred = (self.tokens_consumed / 1000.0) * self.cost_per_1k_tokens
        cost_saved = (self.tokens_saved / 1000.0) * self.cost_per_1k_tokens
        cache_hit_rate = (self.cache_hits / self.total_requests * 100) if self.total_requests > 0 else 0.0

        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_hit_rate_pct": round(cache_hit_rate, 2),
            "tokens_consumed": self.tokens_consumed,
            "tokens_saved": self.tokens_saved,
            "cost_incurred_usd": round(cost_incurred, 4),
            "cost_saved_usd": round(cost_saved, 4)
        }