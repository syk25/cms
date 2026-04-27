import httpx
from app.config import settings

BASE_URL = "https://graph.instagram.com/v21.0"


async def publish_photo(caption: str, image_url: str) -> str:
    """인스타그램 사진 게시물 발행 → permalink 반환"""
    token = settings.instagram_access_token
    user_id = settings.instagram_user_id

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 미디어 컨테이너 생성
        res = await client.post(
            f"{BASE_URL}/{user_id}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": token,
            },
        )
        if res.status_code != 200:
            raise ValueError(f"media 생성 실패 {res.status_code}: {res.text}")
        creation_id = res.json()["id"]

        # 2. 발행
        res = await client.post(
            f"{BASE_URL}/{user_id}/media_publish",
            data={
                "creation_id": creation_id,
                "access_token": token,
            },
        )
        if res.status_code != 200:
            raise ValueError(f"media_publish 실패 {res.status_code}: {res.text}")
        media_id = res.json()["id"]

        # 3. permalink 조회
        res = await client.get(
            f"{BASE_URL}/{media_id}",
            params={"fields": "permalink", "access_token": token},
        )
        if res.status_code != 200:
            raise ValueError(f"permalink 조회 실패 {res.status_code}: {res.text}")
        return res.json()["permalink"]
