import json
from pathlib import Path

from anthropic import Anthropic
from app.config import settings

_client = Anthropic(api_key=settings.anthropic_api_key)

_MEMORY_PATH = Path(__file__).parents[2] / "data" / "user_memory.json"
_MAX_QUERIES = 10
_MAX_INTERESTS = 20

_DEFAULT: dict = {"interests": [], "preferred_tone": "", "recent_queries": []}


def load_memory() -> dict:
    if not _MEMORY_PATH.exists():
        return _DEFAULT.copy()
    with open(_MEMORY_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save(memory: dict) -> None:
    _MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def _extract_keywords(query: str) -> list[str]:
    response = _client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=60,
        messages=[{
            "role": "user",
            "content": f"""다음 문장에서 사용자의 관심사나 글쓰기 주제를 나타내는 핵심 키워드 1~3개를 추출해라.
단어만, 쉼표로 구분, 다른 설명 없이.

문장: {query}

키워드:""",
        }],
    )
    raw = response.content[0].text.strip()
    return [kw.strip() for kw in raw.split(",") if kw.strip()]


def update_memory(query: str) -> None:
    memory = load_memory()

    recent = memory["recent_queries"]
    recent.append(query)
    memory["recent_queries"] = recent[-_MAX_QUERIES:]

    keywords = _extract_keywords(query)
    interests = memory["interests"]
    for kw in keywords:
        if kw not in interests:
            interests.append(kw)
    memory["interests"] = interests[-_MAX_INTERESTS:]

    _save(memory)


def get_memory_context() -> str:
    memory = load_memory()

    parts = []
    if memory["interests"]:
        parts.append("관심사: " + ", ".join(memory["interests"]))
    if memory["preferred_tone"]:
        parts.append("선호 톤: " + memory["preferred_tone"])
    if memory["recent_queries"]:
        parts.append("최근 질문: " + " / ".join(memory["recent_queries"][-3:]))

    return "\n".join(parts)
