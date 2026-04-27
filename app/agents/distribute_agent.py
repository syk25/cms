import json
import re
from typing import TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from app.config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _parse_json(text: str) -> dict:
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    return json.loads(match.group(1) if match else text)


class InstagramContent(BaseModel):
    caption: str
    hashtags: list[str]


class BrunchContent(BaseModel):
    title: str
    body: str


class ThreadContent(BaseModel):
    posts: list[str]


class DistributeState(TypedDict):
    original: str
    instagram: InstagramContent | None
    brunch: BrunchContent | None
    thread: ThreadContent | None


def instagram_node(state: DistributeState) -> dict:
    prompt = f"""다음 원본 글을 인스타그램 게시물로 변환해줘.

원본:
{state["original"]}

반드시 아래 JSON 형식으로만 응답해:
{{
  "caption": "짧고 임팩트 있는 캡션 (300자 이내)",
  "hashtags": ["해시태그1", "해시태그2", ...]
}}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    data = _parse_json(response.content[0].text)
    return {"instagram": InstagramContent(**data)}


def brunch_node(state: DistributeState) -> dict:
    prompt = f"""다음 원본 글을 브런치 아티클로 변환해줘.

원본:
{state["original"]}

반드시 아래 JSON 형식으로만 응답해:
{{
  "title": "아티클 제목",
  "body": "긴 글, 서사형 본문"
}}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    data = _parse_json(response.content[0].text)
    return {"brunch": BrunchContent(**data)}


def thread_node(state: DistributeState) -> dict:
    prompt = f"""다음 원본 글을 스레드(Threads) 형식으로 변환해줘.

원본:
{state["original"]}

반드시 아래 JSON 형식으로만 응답해:
{{
  "posts": ["1번 포스트 (500자 이내)", "2번 포스트 (500자 이내)", ...]
}}

각 포스트는 500자 이내로 작성하고, 전체 3~5개로 구성해."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    data = _parse_json(response.content[0].text)
    return {"thread": ThreadContent(**data)}


def build_distribute_graph():
    graph = StateGraph(DistributeState)

    graph.add_node("instagram", instagram_node)
    graph.add_node("brunch", brunch_node)
    graph.add_node("thread", thread_node)

    graph.add_edge(START, "instagram")
    graph.add_edge(START, "brunch")
    graph.add_edge(START, "thread")

    graph.add_edge("instagram", END)
    graph.add_edge("brunch", END)
    graph.add_edge("thread", END)

    return graph.compile()


distribute_graph = build_distribute_graph()


async def distribute_content(original: str) -> dict:
    initial_state: DistributeState = {
        "original": original,
        "instagram": None,
        "brunch": None,
        "thread": None,
    }
    result = await distribute_graph.ainvoke(initial_state)
    return {
        "instagram": result["instagram"].model_dump(),
        "brunch": result["brunch"].model_dump(),
        "thread": result["thread"].model_dump(),
    }
