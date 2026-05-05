from app.db.supabase_client import get_supabase


def get_content(content_id: str) -> dict | None:
    db = get_supabase()
    result = db.table("contents").select("*").eq("id", content_id).execute()
    return result.data[0] if result.data else None


def link_raw_contents(content_id: str, raw_content_ids: list[str]) -> None:
    if not raw_content_ids:
        return
    db = get_supabase()
    rows = [{"content_id": content_id, "raw_content_id": rid} for rid in raw_content_ids]
    db.table("content_sources").insert(rows).execute()


def save_content(text: str, tags: list[str]) -> dict:
    db = get_supabase()
    row = {"text": text, "tags": tags}
    result = db.table("contents").insert(row).execute()
    return result.data[0]


def update_embedding_id(content_id: str, embedding_id: str) -> None:
    db = get_supabase()
    db.table("contents").update({"embedding_id": embedding_id}).eq(
        "id", content_id
    ).execute()
