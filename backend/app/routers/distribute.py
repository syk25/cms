import urllib.parse

import anthropic
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.distribute_agent import distribute_content
from app.config import settings
from app.db.contents_repo import get_content
from app.db.publications_repo import save_publication, update_publication_status
from app.services.instagram import publish_photo

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

router = APIRouter(prefix="/distribute", tags=["distribute"])


class ConvertRequest(BaseModel):
    content_id: str


class ConvertResponse(BaseModel):
    content_id: str
    instagram: dict
    brunch: dict
    thread: dict


class PublishRequest(BaseModel):
    content_id: str
    caption: str
    hashtags: list[str]
    image_url: str


class BrunchPublishRequest(BaseModel):
    content_id: str
    title: str
    body: str


class ThreadPublishRequest(BaseModel):
    content_id: str
    posts: list[str]


class PublishResponse(BaseModel):
    publication_id: str
    status: str
    published_url: str | None


class ImagePromptRequest(BaseModel):
    caption: str
    hashtags: list[str]


class ImagePromptResponse(BaseModel):
    prompt: str
    image_url: str


@router.post("/image-prompt", response_model=ImagePromptResponse)
def generate_image_prompt(req: ImagePromptRequest):
    """캡션 → 영어 이미지 프롬프트 생성 → Pollinations URL 반환"""
    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=120,
        messages=[{
            "role": "user",
            "content": (
                f"다음 인스타그램 캡션을 바탕으로 이미지 생성에 적합한 영어 프롬프트를 만들어줘.\n\n"
                f"캡션: {req.caption}\n"
                f"해시태그: {', '.join(req.hashtags)}\n\n"
                "규칙:\n"
                "- 영어로만 작성\n"
                "- 60단어 이내\n"
                "- 사진 스타일, 분위기, 색감 포함\n"
                "- 프롬프트 텍스트만 출력, 다른 설명 없이"
            ),
        }],
    )
    prompt = response.content[0].text.strip()
    encoded = urllib.parse.quote(prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1080&nologo=true"
    return ImagePromptResponse(prompt=prompt, image_url=image_url)


@router.post("/convert", response_model=ConvertResponse)
async def convert(req: ConvertRequest):
    """원본 → 플랫폼별 변환 (LangGraph Multi-Agent 병렬 실행)"""
    content = get_content(req.content_id)
    if not content:
        raise HTTPException(status_code=404, detail="content not found")

    result = await distribute_content(original=content["text"])
    return ConvertResponse(content_id=req.content_id, **result)


@router.post("/publish/brunch", response_model=PublishResponse)
async def publish_brunch(req: BrunchPublishRequest):
    """브런치 변환 결과 DB 저장"""
    pub = save_publication(
        content_id=req.content_id,
        platform="brunch",
        text=f"# {req.title}\n\n{req.body}",
        status="converted",
    )
    return PublishResponse(publication_id=pub["id"], status="converted", published_url=None)


@router.post("/publish/thread", response_model=PublishResponse)
async def publish_thread(req: ThreadPublishRequest):
    """스레드 변환 결과 DB 저장"""
    pub = save_publication(
        content_id=req.content_id,
        platform="thread",
        text="\n---\n".join(req.posts),
        status="converted",
    )
    return PublishResponse(publication_id=pub["id"], status="converted", published_url=None)


@router.post("/publish/instagram", response_model=PublishResponse)
async def publish_instagram(req: PublishRequest):
    """인스타그램 발행 + publications 테이블 저장"""
    full_caption = req.caption + "\n\n" + " ".join(f"#{t}" for t in req.hashtags)

    pub = save_publication(
        content_id=req.content_id,
        platform="instagram",
        text=full_caption,
        status="converted",
    )
    pub_id = pub["id"]

    if not settings.instagram_access_token:
        return PublishResponse(
            publication_id=pub_id, status="converted", published_url=None
        )

    try:
        url = await publish_photo(caption=full_caption, image_url=req.image_url)
        update_publication_status(pub_id, status="published", published_url=url)
        return PublishResponse(publication_id=pub_id, status="published", published_url=url)
    except Exception as e:
        update_publication_status(pub_id, status="failed")
        raise HTTPException(status_code=502, detail=str(e))
