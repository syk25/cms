"use client";

import { useState } from "react";
import IngestTab from "@/components/ingest-tab";
import CowriteTab from "@/components/cowrite-tab";
import DistributeTab from "@/components/distribute-tab";

const TABS = ["글감", "글쓰기", "발행"] as const;
type Tab = (typeof TABS)[number];

export default function AppShell() {
  const [tab, setTab] = useState<Tab>("글감");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [contentId, setContentId] = useState<string | null>(null);

  function handleGoToWrite(ids: string[]) {
    setSelectedIds(ids);
    setTab("글쓰기");
  }

  function handleFinalize(id: string) {
    setContentId(id);
    setTab("발행");
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="border-b border-border px-6 py-3 flex items-center gap-3 shrink-0">
        <span className="font-bold text-base tracking-tight">Inkflow</span>
        <span className="text-xs text-muted-foreground hidden sm:block">
          AI 콘텐츠 자동화
        </span>
        {contentId && (
          <span className="ml-auto text-xs text-muted-foreground font-mono">
            content: {contentId.slice(0, 8)}…
          </span>
        )}
      </header>

      {/* Tab nav */}
      <nav className="border-b border-border px-6 shrink-0">
        <div className="flex">
          {TABS.map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                tab === t
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </nav>

      {/* Tab content */}
      <main className="flex-1 p-6 overflow-auto">
        {tab === "글감" && <IngestTab onGoToWrite={handleGoToWrite} />}
        {tab === "글쓰기" && (
          <CowriteTab
            initialSelectedIds={selectedIds}
            onFinalize={handleFinalize}
          />
        )}
        {tab === "발행" && <DistributeTab contentId={contentId} />}
      </main>
    </div>
  );
}
