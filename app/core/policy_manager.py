import yaml
from typing import Dict, Any
from pathlib import Path

class PolicyManager:
    def __init__(self, config_path: str = "app/config.yaml"):
        # Use Pathlib to ensure it finds the file no matter where you run the script from
        self.config_path = Path(__file__).resolve().parent.parent / "config.yaml"
        self.policies = self._load_policies()

    def _load_policies(self) -> Dict[str, Any]:
        """Reads the config.yaml file and returns the policies dictionary."""
        try:
            with open(self.config_path, "r") as file:
                data = yaml.safe_load(file)
                return data.get("policies", {})
        except FileNotFoundError:
            print(f"Error: Configuration file not found at {self.config_path}")
            return {}
        except yaml.YAMLError as exc:
            print(f"Error parsing YAML file: {exc}")
            return {}

    def get_policy(self, scenario: str) -> Dict[str, Any]:
        """
        Returns the policy rules for a specific scenario.
        Provides a highly restrictive fallback if the scenario is unrecognized.
        """
        fallback_policy = {
            "model": "gpt-4o-mini",
            "max_latency_ms": 500,
            "pii_action": "BLOCK",
            "hallucination_threshold": 0.95,
            "ambiguity_action": "ESCALATE",
            "semantic_cache_enabled": False, 
            "similarity_threshold": 0.95
        }
        return self.policies.get(scenario, fallback_policy)

# To test it locally, you can run this file directly:
if __name__ == "__main__":
    pm = PolicyManager(config_path="../config.yaml")
    print("Loaded Policy for Finance:", pm.get_policy("scenario_c_finance"))