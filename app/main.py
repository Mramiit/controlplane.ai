"""
File: app/main.py
Project: ControlPlane.ai Prototype
Contributors: Rahul and Amit

Description:
FastAPI entry point. Routes incoming Streamlit POST requests to the GatewayEngine.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from app.core.engine import GatewayEngine

app = FastAPI(title="ControlPlane.ai Gateway")

# Initialize the engine globally so the cache persists between requests
engine = GatewayEngine()

# 1. We updated this model to expect the exact JSON Streamlit is sending
class ChatRequest(BaseModel):
    prompt: str
    scenario: str

# 2. We updated the endpoint URL to exactly match Streamlit's request
@app.post("/process")
async def process_endpoint(request: ChatRequest):
    
    # Pass the prompt and scenario directly to our dynamic engine
    result = engine.process(request.prompt, request.scenario)
    
    return result