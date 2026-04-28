# app/agents/cowrite_agent.py

import anthropic
from anthropic import AsyncAnthropic
from app.config import settings
from app.db.contents_repo import save_content, update_embedding_id, link_raw_contents
from app.services.embedding import embed_content

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
async_client = AsyncAnthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """당신은 글쓰기 파트너입니다.
사용자가 선택한 주제와 관련 글감을 바탕으로 초안을 작성하고,
사용자 피드백을 반영해 함께 퇴고합니다.
원본은 플랫폼 종속 없이 완성도 높은 글로 작성합니다.

[출력 규칙]
- 글 본문만 출력한다.
- "초안입니다", "수정이 필요하면", "피드백 주시면" 같은 메타 문구는 절대 포함하지 않는다.
- 인사말·설명·안내 없이 글 내용으로 바로 시작한다."""


async def cowrite_draft(
    topic: str,
    related_contents: list[dict],
    history: list[dict],
) -> dict:
    """
    Co-writing Agent — 초안 생성 및 멀티턴 퇴고

    Args:
        topic: 사용자가 선택한 주제
        related_contents: RAG로 검색된 글감 목록 [{"text": str, "tags": list}, ...]
        history: 대화 히스토리 (첫 호출 시 [], 퇴고 시 누적 전달)

    Returns:
        {"draft": str, "history": list[dict]}
    """
    # 첫 호출 (history 비어있음) → 초안 생성 요청 구성
    if not history:
        contents_text = "\n".join(f"- {c['text'][:200]}" for c in related_contents)
        user_message = (
            f"주제: {topic}\n\n"
            f"관련 글감:\n{contents_text}\n\n"
            "위 글감을 바탕으로 초안을 작성해줘."
        )
    else:
        # 퇴고 호출 — 마지막 user 메시지가 이미 history에 추가된 상태로 전달
        user_message = None

    if user_message:
        history.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=history,
    )

    draft = response.content[0].text
    history.append({"role": "assistant", "content": draft})

    return {"draft": draft, "history": history}


async def stream_cowrite(messages: list[dict]):
    async with async_client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def finalize_content(
    text: str, topic: str, tags: list[str], raw_content_ids: list[str] = []
) -> dict:
    row = save_content(text=text, tags=tags)
    content_id = row["id"]
    link_raw_contents(content_id, raw_content_ids)
    embedding_id = embed_content(
        content_id=content_id, text=text, topic=topic, tags=tags
    )
    update_embedding_id(content_id=content_id, embedding_id=embedding_id)
    return {"content_id": content_id, "embedding_id": embedding_id}
