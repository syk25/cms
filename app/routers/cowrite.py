from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.cowrite_agent import cowrite_draft, finalize_content
from app.agents.judge_agent import judge_draft

router = APIRouter(prefix="/cowrite", tags=["cowrite"])


class DraftRequest(BaseModel):
    topic: str
    related_contents: list[dict]  # RAG 검색 결과


class ReviseRequest(BaseModel):
    feedback: str
    history: list[dict]


class CowriteResponse(BaseModel):
    draft: str
    history: list[dict]


class FinalizeRequest(BaseModel):
    text: str
    topic: str
    tags: list[str] = []


class FinalizeResponse(BaseModel):
    content_id: str
    embedding_id: str


class JudgeRequest(BaseModel):
    topic: str
    draft: str
    related_contents: list[dict]


class JudgeResponse(BaseModel):
    scores: dict
    feedback: str
    passed: bool


@router.post("/finalize", response_model=FinalizeResponse)
async def finalize(req: FinalizeRequest):
    """원본 확정 — Supabase contents 저장 + ChromaDB 임베딩"""
    return await finalize_content(text=req.text, topic=req.topic, tags=req.tags)


@router.post("/judge", response_model=JudgeResponse)
async def judge(req: JudgeRequest):
    """LLM-as-a-judge — 초안 품질 평가"""
    return await judge_draft(
        topic=req.topic,
        draft=req.draft,
        related_contents=req.related_contents,
    )


@router.post("/draft", response_model=CowriteResponse)
async def create_draft(req: DraftRequest):
    """초안 생성 — history=[]로 첫 호출"""
    return await cowrite_draft(
        topic=req.topic,
        related_contents=req.related_contents,
        history=[],
    )


@router.post("/revise", response_model=CowriteResponse)
async def revise_draft(req: ReviseRequest):
    """퇴고 — 프론트에서 history + 피드백 같이 보냄"""
    req.history.append({"role": "user", "content": req.feedback})
    return await cowrite_draft(
        topic="",
        related_contents=[],
        history=req.history,
    )
