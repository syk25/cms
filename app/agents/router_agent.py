from anthropic import Anthropic, AsyncAnthropic
from app.config import settings
from app.services.topic_agent import recommend_topics
from app.services.embedding import search_raw_contents
from app.services.memory import update_memory, get_memory_context

client = Anthropic(api_key=settings.anthropic_api_key)
async_client = AsyncAnthropic(api_key=settings.anthropic_api_key)

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


async def stream_route(query: str, memory_context: str = ""):
    """첫 줄에 intent를 yield하고, 이후 LLM 응답을 스트리밍한다."""
    update_memory(query)
    context = memory_context or get_memory_context()
    intent = _classify_intent(query)

    yield f"{intent}\n"

    if intent == "RECOMMEND":
        results = search_raw_contents(query, n_results=5)
        if not results:
            yield "관련 글감을 찾지 못했어요. 글감을 먼저 추가해주세요."
            return
        context_text = "\n\n".join([f"[{r['category']}] {r['text']}" for r in results])
        memory_section = f"\n\n사용자 컨텍스트:\n{context}" if context else ""
        content = (
            f"다음은 사용자의 글감 목록입니다:{memory_section}\n\n"
            f"{context_text}\n\n"
            f"사용자 질문: {query}\n\n"
            "위 글감들을 바탕으로 글쓰기 주제 3가지를 추천해주세요.\n"
            "각 주제는 제목과 한 줄 설명으로 구성해주세요."
        )
        stream_kwargs: dict = dict(model="claude-haiku-4-5", max_tokens=1000,
                                   messages=[{"role": "user", "content": content}])
    else:
        system = "짧고 명확하게 답변한다."
        if context:
            system += f"\n\n사용자 컨텍스트:\n{context}"
        stream_kwargs = dict(model="claude-haiku-4-5", max_tokens=500, system=system,
                             messages=[{"role": "user", "content": query}])

    async with async_client.messages.stream(**stream_kwargs) as stream:
        async for text in stream.text_stream:
            yield text


def route(query: str, memory_context: str = "") -> dict:
    update_memory(query)
    context = memory_context or get_memory_context()

    intent = _classify_intent(query)

    if intent == "RECOMMEND":
        response = recommend_topics(query, memory_context=context)
    else:
        response = _answer_directly(query, context)

    return {"intent": intent, "response": response}
