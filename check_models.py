# File: check_models.py
# Purpose: Queries the Groq API to retrieve a list of all models this specific API key is authorized to use.
# Completed by: Rahul - Implemented API model list retrieval to bypass 404 access restrictions.

import os
from dotenv import load_dotenv
from groq import Groq

# Load the environment variables
load_dotenv(override=True)

# Connect to Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("\n=== HERE ARE YOUR AUTHORIZED MODELS ===")
try:
    models = client.models.list().data
    for m in models:
        print(f"-> {m.id}")
except Exception as e:
    print(f"Failed to fetch models: {e}")
print("=======================================\n")