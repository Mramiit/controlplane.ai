from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.api.dependencies import get_scenario
from app.core.engine import ControlPlaneEngine

router = APIRouter()
engine = ControlPlaneEngine(config_path="app/config.yaml")

class ChatRequest(BaseModel):
    prompt: str

@router.post("/v1/chat/completions")
async def process_chat(request: ChatRequest, scenario: str = Depends(get_scenario)):
    """
    Acts as the reverse proxy gateway, evaluating prompts against the active scenario guardrails.
    """
    result = await engine.process_request(prompt=request.prompt, scenario=scenario)
    return result