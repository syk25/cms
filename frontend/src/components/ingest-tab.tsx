"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import * as api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  onGoToWrite: (selectedIds: string[]) => void;
}

const PAGE_SIZE = 20;

type UsedFilter = "all" | "used" | "unused";

export default function IngestTab({ onGoToWrite }: Props) {
  const [items, setItems] = useState<api.RawContent[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncEvent, setSyncEvent] = useState<api.SyncEvent | null>(null);
  const [keyword, setKeyword] = useState("");
  const [pendingKeyword, setPendingKeyword] = useState("");
  const [usedFilter, setUsedFilter] = useState<UsedFilter>("all");
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const syncCtrlRef = useRef<AbortController | null>(null);

  const load = useCallback(async (pg: number, kw: string, uf: UsedFilter) => {
    setLoading(true);
    try {
      const data = await api.getContents(PAGE_SIZE, pg * PAGE_SIZE, kw, uf);
      setItems(data.items);
      setTotal(data.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(page, keyword, usedFilter);
  }, [load, page, keyword, usedFilter]);

  function handleSearch() {
    setKeyword(pendingKeyword);
    setPage(0);
  }

  function handleUsedFilter(uf: UsedFilter) {
    setUsedFilter(uf);
    setPage(0);
  }

  function handleSync() {
    syncCtrlRef.current?.abort();
    setSyncing(true);
    setSyncEvent(null);
    syncCtrlRef.current = api.syncNotion((e) => {
      setSyncEvent(e);
      if (e.type === "done" || e.type === "error") {
        setSyncing(false);
        load(0, keyword, usedFilter);
        setPage(0);
      }
    });
  }

  async function handleClear() {
    if (!confirm("모든 글감을 삭제하시겠습니까? 되돌릴 수 없습니다.")) return;
    await api.clearContents();
    setItems([]);
    setTotal(0);
    setSelected(new Set());
    setSyncEvent(null);
  }

  function toggleSelect(id: string) {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const pageCount = Math.ceil(total / PAGE_SIZE);

  const syncProgress =
    syncEvent?.type === "progress"
      ? Math.round(((syncEvent.processed ?? 0) / (syncEvent.total ?? 1)) * 100)
      : syncEvent?.type === "done" ? 100 : 0;

  const syncLabel =
    !syncEvent ? "Notion에 연결 중..." :
    syncEvent.type === "start" ? "연결 중..." :
    syncEvent.type === "pages_fetched" ? `페이지 ${syncEvent.total}개 발견. 분류 중...` :
    syncEvent.type === "progress" ? `${syncEvent.processed} / ${syncEvent.total} 페이지 처리 중` :
    syncEvent.type === "done" ? `완료 — ${syncEvent.imported}개 추가, ${syncEvent.skipped}개 스킵` :
    syncEvent.type === "error" ? `오류: ${syncEvent.message}` : "";

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 flex-wrap">
        <Button onClick={handleSync} disabled={syncing} size="sm">
          {syncing ? (
            <span className="flex items-center gap-1.5">
              <svg className="size-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              동기화 중...
            </span>
          ) : "Notion 동기화"}
        </Button>
        <Button
          variant="destructive"
          size="sm"
          onClick={handleClear}
          disabled={syncing || loading || total === 0}
        >
          초기화
        </Button>
        <span className="ml-auto text-sm text-muted-foreground">
          총 {total}개
        </span>
      </div>

      {/* Sync progress */}
      {(syncing || syncEvent?.type === "done") && (
        <div className="space-y-1.5 p-3 rounded-lg border border-border bg-muted/30">
          <Progress value={syncProgress} className="h-1.5" />
          <p className="text-xs text-muted-foreground">{syncLabel}</p>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        <div className="flex gap-1.5 flex-1 max-w-xs">
          <Input
            placeholder="제목 또는 본문 검색..."
            value={pendingKeyword}
            onChange={e => setPendingKeyword(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSearch()}
          />
          <Button variant="outline" size="sm" onClick={handleSearch}>
            검색
          </Button>
        </div>
        <div className="flex rounded-lg border border-border overflow-hidden text-sm">
          {(["all", "unused", "used"] as UsedFilter[]).map(v => (
            <button
              key={v}
              onClick={() => handleUsedFilter(v)}
              className={`px-3 py-1.5 transition-colors ${
                usedFilter === v
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted text-muted-foreground"
              }`}
            >
              {v === "all" ? "전체" : v === "unused" ? "미사용" : "사용됨"}
            </button>
          ))}
        </div>
      </div>

      {/* Content grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="rounded-xl border border-border bg-card p-4 space-y-2 animate-pulse">
              <div className="h-3.5 bg-muted rounded w-2/3" />
              <div className="h-2.5 bg-muted rounded w-1/3" />
              <div className="space-y-1.5 mt-2">
                <div className="h-2 bg-muted rounded" />
                <div className="h-2 bg-muted rounded w-5/6" />
                <div className="h-2 bg-muted rounded w-4/6" />
              </div>
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-20 text-muted-foreground text-sm">
          {total === 0 && !keyword && usedFilter === "all"
            ? "Notion 동기화 버튼으로 글감을 가져오세요."
            : "검색 결과가 없습니다."}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {items.map(item => (
            <ContentCard
              key={item.id}
              item={item}
              selected={selected.has(item.id)}
              onToggle={() => toggleSelect(item.id)}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {pageCount > 1 && (
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0 || loading}
          >
            이전
          </Button>
          <span className="text-sm text-muted-foreground">
            {page + 1} / {pageCount}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(p => Math.min(pageCount - 1, p + 1))}
            disabled={page >= pageCount - 1 || loading}
          >
            다음
          </Button>
        </div>
      )}

      {/* Floating action bar */}
      {selected.size > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 rounded-xl border border-border bg-card px-5 py-3 shadow-2xl">
          <span className="text-sm font-medium">{selected.size}개 선택됨</span>
          <Button size="sm" onClick={() => onGoToWrite([...selected])}>
            선택 글감으로 글쓰기 →
          </Button>
          <button
            className="text-xs text-muted-foreground hover:text-foreground"
            onClick={() => setSelected(new Set())}
          >
            해제
          </button>
        </div>
      )}
    </div>
  );
}

function ContentCard({
  item,
  selected,
  onToggle,
}: {
  item: api.RawContent;
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <Card
      className={`cursor-pointer transition-all hover:ring-2 hover:ring-border ${
        selected ? "ring-2 ring-primary" : ""
      }`}
      onClick={onToggle}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start gap-2">
          <input
            type="checkbox"
            checked={selected}
            onChange={onToggle}
            onClick={e => e.stopPropagation()}
            className="mt-0.5 size-3.5 shrink-0 accent-primary"
          />
          <div className="flex-1 min-w-0">
            <CardTitle className="text-sm line-clamp-1">
              {item.title || "(제목 없음)"}
            </CardTitle>
            <div className="flex items-center gap-1 mt-1.5 flex-wrap">
              <Badge
                variant="outline"
                className={`text-xs px-1.5 py-0 ${
                  item.source === "NOTION"
                    ? "border-violet-500/40 text-violet-400"
                    : "border-emerald-500/40 text-emerald-400"
                }`}
              >
                {item.source}
              </Badge>
              <Badge
                variant="outline"
                className={`text-xs px-1.5 py-0 ${
                  item.is_used
                    ? "border-emerald-500/30 text-emerald-400"
                    : "border-zinc-600/40 text-zinc-500"
                }`}
              >
                {item.is_used ? "사용됨" : "미사용"}
              </Badge>
              {item.category && (
                <Badge variant="outline" className="text-xs px-1.5 py-0">
                  {item.category}
                </Badge>
              )}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed">
          {item.text}
        </p>
        {item.tags?.length > 0 && (
          <div className="flex gap-1 mt-2 flex-wrap">
            {item.tags.slice(0, 5).map(tag => (
              <span key={tag} className="text-xs text-muted-foreground/70">
                #{tag}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
