from anthropic import Anthropic
from app.config import settings
from app.services.topic_agent import recommend_topics
from app.services.memory import update_memory, get_memory_context

client = Anthropic(api_key=settings.anthropic_api_key)

_INTENT_PROMPT = """\
사용자 입력을 보고 의도를 하나만 골라라.

RECOMMEND: 글쓰기 주제 추천 요청
QUESTION: 개념·사실 질문
SUMMARIZE: 내용 요약 요청

사용자 입력: {query}

의도 (RECOMMEND / QUESTION / SUMMARIZE 중 하나만):"""


def _classify_intent(query: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=20,
        messages=[{"role": "user", "content": _INTENT_PROMPT.format(query=query)}],
    )
    raw = response.content[0].text.strip().upper()
    if raw not in ("RECOMMEND", "QUESTION", "SUMMARIZE"):
        return "RECOMMEND"
    return raw


def _answer_directly(query: str, memory_context: str) -> str:
    system = "짧고 명확하게 답변한다."
    if memory_context:
        system += f"\n\n사용자 컨텍스트:\n{memory_context}"

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=500,
        system=system,
        messages=[{"role": "user", "content": query}],
    )
    return response.content[0].text


def route(query: str, memory_context: str = "") -> dict:
    update_memory(query)
    context = memory_context or get_memory_context()

    intent = _classify_intent(query)

    if intent == "RECOMMEND":
        response = recommend_topics(query, memory_context=context)
    else:
        response = _answer_directly(query, context)

    return {"intent": intent, "response": response}
