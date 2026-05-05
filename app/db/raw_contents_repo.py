from app.db.supabase_client import get_supabase


def save_raw_content(
    text: str,
    source: str,
    category_id: str | None,
    tags: list[str],
    embedding_id: str | None = None,
) -> dict:
    db = get_supabase()
    row = {
        "text": text,
        "source": source,
        "category_id": category_id,
        "tags": tags,
        "embedding_id": embedding_id,
    }
    result = db.table("raw_contents").insert(row).execute()
    return result.data[0]


def get_category_id_by_name(category_name: str) -> str | None:
    db = get_supabase()
    result = (
        db.table("categories")
        .select("id")
        .eq("category_name", category_name)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["id"]
    return None


def count_raw_contents() -> int:
    db = get_supabase()
    result = db.table("raw_contents").select("id", count="exact").execute()
    return result.count or 0


def get_all_raw_contents(limit: int = 100) -> list[dict]:
    db = get_supabase()
    result = (
        db.table("raw_contents")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data
