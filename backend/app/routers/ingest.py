import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.agents.notion_import import run_notion_import, stream_notion_import
from app.db.raw_contents_repo import get_all_raw_contents, count_raw_contents, truncate_raw_contents

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/notion/stream")
def ingest_notion_stream():
    total_before = count_raw_contents()

    def generate():
        yield json.dumps({"type": "start", "total_before": total_before}) + "\n"
        try:
            for event in stream_notion_import():
                yield json.dumps(event) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/notion")
def ingest_notion() -> dict:
    try:
        total_before = count_raw_contents()
        result = run_notion_import()
        return {
            "total_before": total_before,
            "fetched": result["fetched"],
            "imported": result["imported"],
            "skipped": result["skipped"],
            "items": result["items"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/contents")
def clear_contents() -> dict:
    truncate_raw_contents()
    return {"status": "cleared"}


@router.get("/contents")
def list_contents(
    limit: int = 20,
    offset: int = 0,
    search: str = "",
    is_used: str = "",
) -> dict:
    is_used_bool: bool | None = None
    if is_used == "true":
        is_used_bool = True
    elif is_used == "false":
        is_used_bool = False
    total = count_raw_contents(keyword=search, is_used=is_used_bool)
    results = get_all_raw_contents(limit=limit, offset=offset, keyword=search, is_used=is_used_bool)
    return {"total": total, "items": results}
