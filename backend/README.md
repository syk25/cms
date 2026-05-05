# Inkflow — Backend

FastAPI 기반 콘텐츠 매니지먼트 API 서버.

## 로컬 실행

```bash
# 1. 의존성 설치 (uv 필요: https://docs.astral.sh/uv/)
uv sync

# 2. 환경변수 설정
cp .env.example .env
# .env 파일에 아래 키 입력:
#   ANTHROPIC_API_KEY, VOYAGE_API_KEY
#   SUPABASE_URL, SUPABASE_KEY
#   NOTION_API_KEY, NOTION_DATABASE_ID

# 3. 서버 실행
uv run uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

## 주요 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/ingest/notion` | Notion DB 증분 import + 분류 |
| `GET` | `/ingest/contents` | 글감 목록 조회 |
| `POST` | `/discovery/route` | 주제 추천 (RAG) |
| `POST` | `/cowrite/draft` | 초안 생성 |
| `POST` | `/cowrite/finalize` | 원본 확정 + DB 저장 |
| `POST` | `/distribute/convert` | 플랫폼별 변환 (LangGraph Fan-out) |
| `POST` | `/distribute/publish/instagram` | Instagram 발행 |

## 배포 (Fly.io)

```bash
fly deploy --config fly.toml
# → https://inkflow-api.fly.dev
```

## 기술 스택

| 항목 | 기술 |
|------|------|
| 언어 | Python 3.11 + uv |
| 프레임워크 | FastAPI |
| LLM | Claude Haiku 4.5 (Anthropic) |
| Agent | LangGraph |
| 임베딩 | Voyage AI (voyage-3) |
| 벡터 DB | ChromaDB |
| 관계형 DB | Supabase (PostgreSQL) |
