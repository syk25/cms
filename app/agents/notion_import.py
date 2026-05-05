from app.db.notion_repo import (
    get_last_imported_at,
    fetch_notion_pages,
    extract_page_text,
)
from app.db.notion_sources_repo import (
    upsert_notion_source,
    get_notion_source_by_page_id,
)
from app.db.raw_contents_repo import save_raw_content, get_category_id_by_name
from app.agents.classify_agent import suggest_categories, classify_content
from app.db.categories_repo import get_all_categories, save_categories, is_empty


def run_notion_import() -> dict:
    """Notion DB에서 글감을 가져와 분류 후 Supabase에 저장."""
    last_imported_at = get_last_imported_at()
    pages = fetch_notion_pages(last_imported_at)

    if not pages:
        return {"fetched": 0, "imported": 0, "skipped": 0, "items": []}

    texts = []
    for page in pages:
        text = extract_page_text(page["id"])
        if text.strip():
            texts.append(text)

    if is_empty() and texts:
        suggested = suggest_categories(texts)
        save_categories(suggested)

    categories = [c["category_name"] for c in get_all_categories()]

    results = []
    imported = 0
    skipped = 0
    for page in pages:
        text = extract_page_text(page["id"])
        if not text.strip():
            continue

        classified = classify_content(text, categories)
        category_id = (
            get_category_id_by_name(classified["category"])
            if classified["category"]
            else None
        )

        existing = get_notion_source_by_page_id(page["id"])
        if existing:
            skipped += 1
            results.append(existing)
        else:
            saved = save_raw_content(
                text=text,
                source="notion",
                category_id=category_id,
                tags=classified["tags"],
            )
            upsert_notion_source(
                raw_content_id=saved["id"],
                notion_page_id=page["id"],
                notion_url=page["url"],
            )
            imported += 1
            results.append(saved)

    return {"fetched": len(pages), "imported": imported, "skipped": skipped, "items": results}
