from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="ControlPlane.ai Gateway",
    description="Multi-Scenario AI Governance Middleware",
    version="1.0.0"
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    # Runs the FastAPI server on port 8000
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)