from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents.router_agent import route

router = APIRouter(prefix="/discovery", tags=["discovery"])


class QueryRequest(BaseModel):
    query: str
    memory_context: str = ""


@router.post("/route")
def route_query(req: QueryRequest) -> dict:
    try:
        return route(req.query, memory_context=req.memory_context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
