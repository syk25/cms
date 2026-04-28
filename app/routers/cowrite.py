from anthropic import AsyncAnthropic
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agents.cowrite_agent import cowrite_draft, finalize_content, stream_cowrite
from app.agents.judge_agent import judge_draft
from app.config import settings

router = APIRouter(prefix="/cowrite", tags=["cowrite"])

_async_client = AsyncAnthropic(api_key=settings.anthropic_api_key)

_DISCUSS_SYSTEM = """당신은 글쓰기 파트너입니다. 지금은 초안 작성 전 토의 단계입니다.

역할:
- 사용자가 선택한 주제에 대해 함께 탐색하고 깊이 들어간다.
- 질문으로 구체적인 경험, 감정, 에피소드를 끌어낸다.
- 어떤 각도·관점으로 글을 쓸지 함께 결정한다.

규칙:
- 초안을 절대 쓰지 않는다. 대화로만 진행한다.
- 한 번에 질문 1~2개만. 짧고 구체적으로.
- 충분히 탐색됐다고 판단되면 "이제 초안을 써볼까요?" 라고 자연스럽게 제안한다."""


class DraftRequest(BaseModel):
    topic: str
    related_contents: list[dict]  # RAG 검색 결과
    discuss_notes: str = ""       # 토의 내용 요약


class DiscussRequest(BaseModel):
    topic: str
    history: list[dict] = []
    message: str


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


@router.post("/discuss/stream")
async def discuss_stream(req: DiscussRequest):
    """주제 토의 — 초안 작성 전 멀티턴 대화"""
    if req.history:
        messages = req.history + [{"role": "user", "content": req.message}]
    else:
        messages = [{"role": "user", "content": f"주제: {req.topic}\n\n{req.message}"}]

    async def generate():
        async with _async_client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            system=_DISCUSS_SYSTEM,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/draft/stream")
async def draft_stream(req: DraftRequest):
    contents_text = "\n".join(f"- {c['text'][:200]}" for c in req.related_contents)
    discuss_section = f"\n\n토의에서 나온 내용:\n{req.discuss_notes}" if req.discuss_notes else ""
    user_msg = (
        f"주제: {req.topic}\n\n"
        f"관련 글감:\n{contents_text}"
        f"{discuss_section}\n\n"
        "위를 바탕으로 초안을 작성해줘."
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
