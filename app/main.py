from fastapi import FastAPI
from app.routers import ingest, discovery, cowrite

app = FastAPI(
    title="Content Management Service",
    version="0.1.0",
)

app.include_router(ingest.router)
app.include_router(discovery.router)
app.include_router(cowrite.router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
