from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.distribute_agent import distribute_content
from app.db.contents_repo import get_content

router = APIRouter(prefix="/distribute", tags=["distribute"])


class ConvertRequest(BaseModel):
    content_id: str


class ConvertResponse(BaseModel):
    content_id: str
    instagram: dict
    brunch: dict
    thread: dict


@router.post("/convert", response_model=ConvertResponse)
async def convert(req: ConvertRequest):
    """원본 → 플랫폼별 변환 (LangGraph Multi-Agent 병렬 실행)"""
    content = get_content(req.content_id)
    if not content:
        raise HTTPException(status_code=404, detail="content not found")

    result = await distribute_content(original=content["text"])
    return ConvertResponse(content_id=req.content_id, **result)
