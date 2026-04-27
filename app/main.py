from fastapi import FastAPI

app = FastAPI(
    title="Content Management Service",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}