from app.db.supabase_client import get_supabase


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
