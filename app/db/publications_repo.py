from app.db.supabase_client import get_supabase


def save_publication(
    content_id: str,
    platform: str,
    text: str,
    status: str = "converted",
    published_url: str | None = None,
) -> dict:
    db = get_supabase()
    row = {
        "content_id": content_id,
        "platform": platform,
        "text": text,
        "status": status,
        "published_url": published_url,
    }
    result = db.table("publications").insert(row).execute()
    return result.data[0]


def update_publication_status(
    publication_id: str, status: str, published_url: str | None = None
) -> None:
    db = get_supabase()
    payload: dict = {"status": status}
    if published_url is not None:
        payload["published_url"] = published_url
    db.table("publications").update(payload).eq("id", publication_id).execute()


def get_publications_by_content(content_id: str) -> list[dict]:
    db = get_supabase()
    result = (
        db.table("publications")
        .select("*")
        .eq("content_id", content_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data
