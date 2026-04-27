import json
import anthropic
from app.config import settings  # 기존 프로젝트 import 방식으로 수정

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

JUDGE_SYSTEM_PROMPT = """당신은 글쓰기 평가자입니다.
아래 기준으로 초안을 평가하고 반드시 JSON만 반환하세요. 다른 텍스트 없이 JSON만.

평가 기준:
- topic_relevance: 주제 관련성 (1~5)
- content_usage: 글감 활용도 (1~5)
- readability: 가독성 (1~5)

반환 형식:
{"scores": {"topic_relevance": 0, "content_usage": 0, "readability": 0}, "feedback": "한 줄 피드백"}"""


async def judge_draft(
    topic: str,
    draft: str,
    related_contents: list[dict],
) -> dict:
    """
    LLM-as-a-judge — Co-writing Agent 초안 품질 평가

    Args:
        topic: 주제
        draft: 평가할 초안
        related_contents: 원본 글감 목록

    Returns:
        {"scores": {"topic_relevance": int, "content_usage": int, "readability": int},
         "feedback": str, "passed": bool}
    """
    contents_text = "\n".join(f"- {c['text'][:200]}" for c in related_contents)

    user_message = (
        f"주제: {topic}\n\n" f"사용된 글감:\n{contents_text}\n\n" f"초안:\n{draft}"
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=JUDGE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text
    clean = (
        raw.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    result = json.loads(clean)
    scores = result["scores"]
    avg_score = sum(scores.values()) / len(scores)
    result["passed"] = avg_score >= 3.0  # 평균 3점 이상 통과

    return result
