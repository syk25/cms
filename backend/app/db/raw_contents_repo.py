from app.db.supabase_client import get_supabase


def save_raw_content(
    text: str,
    source: str,
    category_id: str | None,
    tags: list[str],
    title: str | None = None,
    embedding_id: str | None = None,
) -> dict:
    db = get_supabase()
    row = {
        "title": title or None,
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


def count_raw_contents(keyword: str = "", is_used: bool | None = None) -> int:
    db = get_supabase()
    query = db.table("raw_contents").select("id", count="exact")
    if keyword:
        query = query.or_(f"title.ilike.%{keyword}%,text.ilike.%{keyword}%")
    if is_used is not None:
        query = query.eq("is_used", is_used)
    result = query.execute()
    return result.count or 0


def get_all_raw_contents(
    limit: int = 20,
    offset: int = 0,
    keyword: str = "",
    is_used: bool | None = None,
) -> list[dict]:
    db = get_supabase()
    query = (
        db.table("raw_contents")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
    )
    if keyword:
        query = query.or_(f"title.ilike.%{keyword}%,text.ilike.%{keyword}%")
    if is_used is not None:
        query = query.eq("is_used", is_used)
    result = query.execute()
    return result.data


def truncate_raw_contents() -> None:
    db = get_supabase()
    db.table("content_sources").delete().neq("raw_content_id", "00000000-0000-0000-0000-000000000000").execute()
    db.table("notion_sources").delete().neq("raw_content_id", "00000000-0000-0000-0000-000000000000").execute()
    db.table("raw_contents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()


def mark_as_used(ids: list[str]) -> None:
    if not ids:
        return
    db = get_supabase()
    db.table("raw_contents").update({"is_used": True}).in_("id", ids).execute()
