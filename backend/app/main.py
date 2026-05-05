from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import ingest, discovery, cowrite, distribute

app = FastAPI(
    title="Content Management Service",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(discovery.router)
app.include_router(cowrite.router)
app.include_router(distribute.router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
