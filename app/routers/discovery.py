from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agents.router_agent import route, stream_route

router = APIRouter(prefix="/discovery", tags=["discovery"])


class QueryRequest(BaseModel):
    query: str
    memory_context: str = ""


@router.post("/route/stream")
async def route_stream(req: QueryRequest):
    async def generate():
        async for chunk in stream_route(req.query, memory_context=req.memory_context):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/route")
def route_query(req: QueryRequest) -> dict:
    try:
        return route(req.query, memory_context=req.memory_context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
