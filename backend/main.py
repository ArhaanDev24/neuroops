from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.orchestrator import NeuroOrchestrator
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NeuroOps API", version="1.0.0")
orchestrator = NeuroOrchestrator()

class GoalRequest(BaseModel):
    goal: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "NeuroOps"}

@app.post("/execute-goal")
async def execute_goal(request: GoalRequest):
    try:
        logger.info(f"Received goal: {request.goal}")
        result = orchestrator.run(request.goal)
        return result
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)