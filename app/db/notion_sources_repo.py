from app.db.supabase_client import get_supabase


def upsert_notion_source(raw_content_id: str, notion_page_id: str, notion_url: str) -> dict:
    db = get_supabase()
    row = {
        "raw_content_id": raw_content_id,
        "notion_page_id": notion_page_id,
        "notion_url": notion_url,
    }
    result = (
        db.table("notion_sources")
        .upsert(row, on_conflict="notion_page_id")
        .execute()
    )
    return result.data[0]


def get_notion_source_by_page_id(notion_page_id: str) -> dict | None:
    db = get_supabase()
    result = (
        db.table("notion_sources")
        .select("*")
        .eq("notion_page_id", notion_page_id)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]
    return None