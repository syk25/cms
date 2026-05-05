# Inkflow — Frontend

Next.js 기반 콘텐츠 매니지먼트 UI.

## 로컬 실행

```bash
# 1. 의존성 설치
npm install

# 2. 환경변수 설정
cp .env.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

# 3. 개발 서버 실행
npm run dev
# → http://localhost:3000
```

> 백엔드 서버(`localhost:8000`)가 먼저 실행 중이어야 합니다.  
> 백엔드 실행 방법은 [backend/README.md](../backend/README.md) 참고.

## 기술 스택

| 항목 | 기술 |
|------|------|
| 프레임워크 | Next.js 16 (App Router) |
| 언어 | TypeScript |
| 스타일 | Tailwind CSS v4 |
| UI 컴포넌트 | shadcn/ui |
