from anthropic import Anthropic
from app.config import settings
from app.services.embedding import search_raw_contents

client = Anthropic(api_key=settings.anthropic_api_key)


def recommend_topics(query: str, n_results: int = 5, memory_context: str = "") -> str:
    results = search_raw_contents(query, n_results=n_results)

    if not results:
        return "관련 글감을 찾지 못했어요. 글감을 먼저 추가해주세요."

    context = "\n\n".join([f"[{r['category']}] {r['text']}" for r in results])
    memory_section = f"\n\n사용자 컨텍스트:\n{memory_context}" if memory_context else ""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"""다음은 사용자의 글감 목록입니다:{memory_section}

{context}

사용자 질문: {query}

위 글감들을 바탕으로 글쓰기 주제 3가지를 추천해주세요.
각 주제는 제목과 한 줄 설명으로 구성해주세요.""",
            }
        ],
    )

    return response.content[0].text
