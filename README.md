# CMS — Content Management Service

LangGraph Multi-Agent 기반 콘텐츠 매니지먼트 서비스.
초안 하나로 여러 플랫폼(브런치, 인스타그램, 스레드)에 맞는 콘텐츠를 자동 변환·게시하고, 성과 데이터를 통합 관리합니다.

> 14일 MVP 프로젝트 (2026.04.26 ~) — 진행 중

## 기술 스택

- Python 3.11 / FastAPI
- Anthropic Claude (Haiku + Sonnet)
- LangGraph (Multi-Agent 오케스트레이션)
- ChromaDB (벡터 DB) + Supabase (관계형 DB)
- Voyage AI (임베딩)
- Streamlit (UI)
- uv (패키지 매니저)

## 아키텍처 결정 기록 (ADR)

설계·기술 선택의 근거는 [`docs/adr/`](docs/adr/)에 정리되어 있습니다.

- ADR-001: Supabase + ChromaDB 이중 저장
- ADR-002: LangGraph 선택
- ADR-003: Claude Haiku + Sonnet 혼용
- ADR-004: FastAPI 선택
- ADR-005: uv 선택

## 로컬 개발

```bash
# 의존성 설치
uv sync

# 환경변수 설정
cp .env.example .env
# .env에 ANTHROPIC_API_KEY 입력

# 서버 실행
uv run uvicorn app.main:app --reload
```

`http://localhost:8000/docs`에서 API 문서 확인.
