import json
import logging
from app.config import settings
from app.llm.claude_client import ClaudeClient
from app.db.categories_repo import get_all_categories, save_categories, is_empty
from app.db.raw_contents_repo import save_raw_content, get_category_id_by_name


logger = logging.getLogger(__name__)

_client = ClaudeClient(api_key=settings.anthropic_api_key, model="claude-haiku-4-5")


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
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
    try:
        return _parse_json(result["text"])["categories"]
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"suggest_categories 파싱 실패: {e}, 원문: {result['text']}")
        return []


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
    try:
        return _parse_json(result["text"])
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"classify_content 파싱 실패: {e}, 원문: {result['text']}")
        return {"category": None, "tags": []}


def run_ingest_pipeline(texts: list[str], source: str = "direct") -> list[dict]:
    """글감 목록을 받아 분류 후 Supabase에 저장."""
    if is_empty():
        suggested = suggest_categories(texts)
        save_categories(suggested)

    categories = [c["category_name"] for c in get_all_categories()]

    results = []
    for text in texts:
        classified = classify_content(text, categories)
        category_id = (
            get_category_id_by_name(classified["category"])
            if classified["category"]
            else None
        )
        saved = save_raw_content(
            text=text,
            source=source,
            category_id=category_id,
            tags=classified["tags"],
        )
        results.append(saved)

    return results
