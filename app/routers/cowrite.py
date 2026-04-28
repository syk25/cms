from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agents.cowrite_agent import cowrite_draft, finalize_content, stream_cowrite
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
    raw_content_ids: list[str] = []


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
    """원본 확정 — Supabase contents 저장 + ChromaDB 임베딩 + 글감 연결"""
    return await finalize_content(
        text=req.text, topic=req.topic, tags=req.tags, raw_content_ids=req.raw_content_ids
    )


@router.post("/judge", response_model=JudgeResponse)
async def judge(req: JudgeRequest):
    """LLM-as-a-judge — 초안 품질 평가"""
    return await judge_draft(
        topic=req.topic,
        draft=req.draft,
        related_contents=req.related_contents,
    )


@router.post("/draft/stream")
async def draft_stream(req: DraftRequest):
    contents_text = "\n".join(f"- {c['text'][:200]}" for c in req.related_contents)
    user_msg = (
        f"주제: {req.topic}\n\n"
        f"관련 글감:\n{contents_text}\n\n"
        "위 글감을 바탕으로 초안을 작성해줘."
    )
    messages = [{"role": "user", "content": user_msg}]

    async def generate():
        async for chunk in stream_cowrite(messages):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/revise/stream")
async def revise_stream(req: ReviseRequest):
    messages = req.history + [{"role": "user", "content": req.feedback}]

    async def generate():
        async for chunk in stream_cowrite(messages):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")


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
