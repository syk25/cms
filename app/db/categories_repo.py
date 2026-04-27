from app.db.supabase_client import get_supabase


def get_all_categories() -> list[dict]:
    db = get_supabase()
    result = db.table("categories").select("*").execute()
    return result.data


def save_categories(category_names: list[str]) -> list[dict]:
    db = get_supabase()
    rows = [{"category_name": name} for name in category_names]
    result = db.table("categories").upsert(rows, on_conflict="category_name").execute()
    return result.data


def is_empty() -> bool:
    db = get_supabase()
    result = db.table("categories").select("id").limit(1).execute()
    return len(result.data) == 0