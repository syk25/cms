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


def _extract_title(page: dict) -> str:
    """Notion 페이지 properties에서 제목 추출."""
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            parts = prop.get("title", [])
            return parts[0]["plain_text"] if parts else ""
    return ""


def stream_notion_import():
    """Notion import를 실행하며 진행 이벤트를 yield한다."""
    last_imported_at = get_last_imported_at()
    pages = fetch_notion_pages(last_imported_at)

    if not pages:
        yield {"type": "done", "fetched": 0, "imported": 0, "skipped": 0}
        return

    page_bodies: dict[str, str] = {}
    texts = []
    for page in pages:
        body = extract_page_text(page["id"])
        page_bodies[page["id"]] = body
        if body.strip():
            texts.append(body)

    yield {"type": "pages_fetched", "total": len(pages)}

    if is_empty() and texts:
        suggested = suggest_categories(texts)
        save_categories(suggested)

    categories = [c["category_name"] for c in get_all_categories()]

    imported = 0
    skipped = 0

    for i, page in enumerate(pages):
        title = _extract_title(page)
        body = page_bodies[page["id"]]

        if not title.strip() and not body.strip():
            yield {"type": "progress", "processed": i + 1, "total": len(pages)}
            continue

        classified = classify_content(body or title, categories)
        category_id = (
            get_category_id_by_name(classified["category"])
            if classified["category"]
            else None
        )

        existing = get_notion_source_by_page_id(page["id"])
        if existing:
            skipped += 1
        else:
            saved = save_raw_content(
                title=title.strip() or None,
                text=body.strip(),
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

        yield {"type": "progress", "processed": i + 1, "total": len(pages)}

    yield {"type": "done", "fetched": len(pages), "imported": imported, "skipped": skipped}


def run_notion_import() -> dict:
    """Notion DB에서 글감을 가져와 분류 후 Supabase에 저장."""
    last_imported_at = get_last_imported_at()
    pages = fetch_notion_pages(last_imported_at)

    if not pages:
        return {"fetched": 0, "imported": 0, "skipped": 0, "items": []}

    # 본문 캐싱 (extract_page_text 중복 호출 방지)
    page_bodies: dict[str, str] = {}
    texts = []
    for page in pages:
        body = extract_page_text(page["id"])
        page_bodies[page["id"]] = body
        if body.strip():
            texts.append(body)

    if is_empty() and texts:
        suggested = suggest_categories(texts)
        save_categories(suggested)

    categories = [c["category_name"] for c in get_all_categories()]

    results = []
    imported = 0
    skipped = 0
    for page in pages:
        title = _extract_title(page)
        body = page_bodies[page["id"]]

        if not title.strip() and not body.strip():
            continue

        classified = classify_content(body or title, categories)
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
                title=title.strip() or None,
                text=body.strip(),
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
