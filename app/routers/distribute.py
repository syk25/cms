from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.distribute_agent import distribute_content
from app.config import settings
from app.db.contents_repo import get_content
from app.db.publications_repo import save_publication, update_publication_status
from app.services.instagram import publish_photo

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
