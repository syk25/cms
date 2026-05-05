"use client";

import { Button } from "@/components/ui/button";

interface Props {
  onStart: () => void;
}

export default function LandingPage({ onStart }: Props) {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-20 text-center gap-6">
        <div className="space-y-2">
          <p className="text-xs font-medium tracking-widest text-primary uppercase">
            AI Content Automation
          </p>
          <h1 className="text-5xl font-bold tracking-tight">
            🖊️ Inkflow
          </h1>
          <p className="text-lg text-muted-foreground max-w-md mx-auto leading-relaxed">
            글감을 수집하고, AI와 함께 쓰고,
            <br />
            인스타·브런치·스레드에 한 번에 발행하세요.
          </p>
        </div>

        <Button size="lg" onClick={onStart} className="px-8 mt-2">
          시작하기 →
        </Button>

        {/* Feature cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto mt-8 w-full">
          {[
            {
              step: "01",
              title: "수집",
              desc: "Notion에서 글감을 가져오고 AI가 자동 분류합니다.",
            },
            {
              step: "02",
              title: "창작",
              desc: "AI와 토의하고 초안을 함께 쓰고 퇴고합니다.",
            },
            {
              step: "03",
              title: "발행",
              desc: "플랫폼별 포맷으로 변환해 한 번에 발행합니다.",
            },
          ].map(({ step, title, desc }) => (
            <div
              key={step}
              className="rounded-xl border border-border bg-card p-5 text-left space-y-2"
            >
              <p className="text-xs font-mono text-primary">{step}</p>
              <p className="font-semibold">{title}</p>
              <p className="text-xs text-muted-foreground leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        {/* Tech badges */}
        <div className="flex gap-2 flex-wrap justify-center mt-4">
          {[
            "FastAPI",
            "LangGraph",
            "Claude Haiku",
            "Voyage AI",
            "ChromaDB",
            "Supabase",
            "Next.js",
          ].map(tech => (
            <span
              key={tech}
              className="text-xs px-2.5 py-1 rounded-full border border-border text-muted-foreground"
            >
              {tech}
            </span>
          ))}
        </div>
      </main>

      <footer className="text-center py-4 text-xs text-muted-foreground border-t border-border">
        Inkflow — syk25
      </footer>
    </div>
  );
}
