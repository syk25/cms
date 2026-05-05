# ADR-004. FastAPI 선택

- **Status**: Accepted
- **Date**: 2026-04-27

## 결정

웹 프레임워크로 FastAPI 채택 (Flask, Django 검토 후 탈락).

## 이유

1. **비동기 네이티브** — `async def`를 1급으로 지원. LLM API 호출이 2~10초로 느린 환경에서 Multi-Agent 병렬 호출에 유리.
2. **Pydantic 통합** — 요청/응답 자동 검증·직렬화. `app/config.py`의 Pydantic Settings와 일관된 검증 계층 형성.
3. **OpenAPI 자동 생성** — `/docs` Swagger UI 무료 제공. 14일 프로젝트에서 문서화 비용 절감 + 면접·데모 시 시스템 가시성 확보.

## 대안

- **Flask** 탈락 — 비동기 후발주자, 검증·문서화에 외부 라이브러리 필요.
- **Django** 탈락 — ORM·Admin 등 풀스택 오버스펙. LLM API 서버에 불필요.

## 결과 / Trade-off

- (+) LLM 동시 호출에 강함, 타입 안전성 일관, Swagger 자동
- (−) Django 대비 생태계 작음, `async def` ↔ `def` 혼용 시 블로킹 위험 (Day 3~4 LangGraph 통합 시 점검)
