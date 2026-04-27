import json
from app.config import settings
from app.llm.claude_client import ClaudeClient

_client = ClaudeClient(api_key=settings.anthropic_api_key, model="claude-haiku-4-5")


def _parse_json(text: str) -> dict | list:
    """LLM 응답에서 코드블록 제거 후 JSON 파싱."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]  # 첫 줄 (```json) 제거
        text = text.rsplit("```", 1)[0]  # 마지막 ``` 제거
    return json.loads(text.strip())


def suggest_categories(texts: list[str]) -> list[str]:
    combined = "\n\n".join(f"- {t}" for t in texts)
    result = _client.complete(
        prompt=combined,
        system=(
            "너는 콘텐츠 분류 전문가야. "
            "아래 글감들을 분석해서 적절한 카테고리 목록을 5개 이내로 제안해. "
            "반드시 JSON만 반환해. 다른 텍스트 없이. "
            '예: {"categories": ["개발", "일상", "독서"]}'
        ),
        max_tokens=256,
    )
    return _parse_json(result["text"])["categories"]


def classify_content(text: str, categories: list[str]) -> dict:
    result = _client.complete(
        prompt=text,
        system=(
            "너는 콘텐츠 분류 전문가야. "
            f"카테고리 목록: {categories}. "
            "아래 글감을 분석해서 카테고리 1개와 태그 3개 이내를 부여해. "
            "반드시 JSON만 반환해. 다른 텍스트 없이. "
            '예: {"category": "개발", "tags": ["FastAPI", "Python"]}'
        ),
        max_tokens=256,
    )
    return _parse_json(result["text"])
