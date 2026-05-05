from notion_client import Client
from app.config import settings
from app.db.supabase_client import get_supabase
from notion2md.exporter.block import StringExporter
import os

_notion = Client(auth=settings.notion_api_key)


def get_last_imported_at() -> str | None:
    """notion_sources에서 마지막 import 시각 조회."""
    db = get_supabase()
    result = (
        db.table("notion_sources")
        .select("imported_at")
        .order("imported_at", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["imported_at"]
    return None


def fetch_notion_pages(last_imported_at: str | None = None) -> list[dict]:
    """Notion DB에서 페이지 목록 가져오기."""
    params = {"database_id": settings.notion_database_id}
    if last_imported_at:
        params["filter"] = {
            "timestamp": "last_edited_time",
            "last_edited_time": {"after": last_imported_at},
        }
    response = _notion.databases.query(**params)
    return response["results"]


def extract_page_text(page_id: str) -> str:
    """Notion 페이지 블록에서 마크다운으로 추출."""
    os.environ["NOTION_TOKEN"] = settings.notion_token
    return StringExporter(block_id=page_id, output_path="").export()
