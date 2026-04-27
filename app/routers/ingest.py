from fastapi import APIRouter, HTTPException
from app.agents.notion_import import run_notion_import
from app.db.raw_contents_repo import get_all_raw_contents

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/notion")
def ingest_notion() -> dict:
    try:
        results = run_notion_import()
        return {"imported": len(results), "items": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contents")
def list_contents(limit: int = 100) -> dict:
    results = get_all_raw_contents(limit=limit)
    return {"total": len(results), "items": results}
