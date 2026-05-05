"use client";

import { useEffect, useRef, useState } from "react";
import * as api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";

type Phase =
  | "topic"
  | "discussing"
  | "drafting"
  | "draft_ready"
  | "revising"
  | "done";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface Props {
  initialSelectedIds?: string[];
  onFinalize: (contentId: string) => void;
}

export default function CowriteTab({
  initialSelectedIds = [],
  onFinalize,
}: Props) {
  const [phase, setPhase] = useState<Phase>("topic");
  const [topic, setTopic] = useState("");
  const [related, setRelated] = useState<api.RawContent[]>([]);
  const [searching, setSearching] = useState(false);

  // Discuss
  const [discussHistory, setDiscussHistory] = useState<ChatMessage[]>([]);
  const [discussInput, setDiscussInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState("");

  // Draft
  const [draftText, setDraftText] = useState("");
  const [draftHistory, setDraftHistory] = useState<ChatMessage[]>([]);

  // Revise
  const [feedback, setFeedback] = useState("");

  // Judge
  const [judging, setJudging] = useState(false);
  const [judgeResult, setJudgeResult] = useState<api.JudgeResult | null>(null);

  // Finalize
  const [finalizing, setFinalizing] = useState(false);

  const abortRef = useRef<AbortController | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [discussHistory, streamText]);

  async function handleSearch() {
    if (!topic.trim()) return;
    setSearching(true);
    try {
      const res = await api.searchContents(topic);
      setRelated(res.results);
    } finally {
      setSearching(false);
    }
  }

  async function handleDiscuss() {
    if (!discussInput.trim() || streaming) return;
    const userMsg = discussInput.trim();
    setDiscussInput("");

    const newHistory: ChatMessage[] = [
      ...discussHistory,
      { role: "user", content: userMsg },
    ];
    setDiscussHistory(newHistory);
    setStreaming(true);
    setStreamText("");

    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    let fullText = "";
    try {
      await api.readStream(
        "/cowrite/discuss/stream",
        { topic, history: discussHistory, message: userMsg },
        (chunk) => {
          fullText += chunk;
          setStreamText(fullText);
        },
        ctrl.signal
      );
      setDiscussHistory([
        ...newHistory,
        { role: "assistant", content: fullText },
      ]);
      setStreamText("");
    } catch (e) {
      if ((e as Error).name === "AbortError") return;
    } finally {
      setStreaming(false);
    }
  }

  async function handleDraft() {
    setPhase("drafting");
    setDraftText("");
    setJudgeResult(null);

    const discussNotes = discussHistory
      .map(m => `${m.role === "user" ? "나" : "AI"}: ${m.content}`)
      .join("\n");

    const userPrompt =
      `주제: ${topic}\n\n관련 글감:\n` +
      related.map(r => `- ${r.text.slice(0, 200)}`).join("\n") +
      (discussNotes ? `\n\n토의 내용:\n${discussNotes}` : "") +
      "\n\n위를 바탕으로 초안을 작성해줘.";

    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    let fullDraft = "";
    try {
      await api.readStream(
        "/cowrite/draft/stream",
        { topic, related_contents: related, discuss_notes: discussNotes },
        (chunk) => {
          fullDraft += chunk;
          setDraftText(fullDraft);
        },
        ctrl.signal
      );
      setDraftHistory([
        { role: "user", content: userPrompt },
        { role: "assistant", content: fullDraft },
      ]);
      setPhase("draft_ready");
    } catch (e) {
      if ((e as Error).name !== "AbortError") setPhase("topic");
    }
  }

  async function handleRevise() {
    if (!feedback.trim()) return;
    const prevFeedback = feedback;
    setFeedback("");
    setPhase("revising");

    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    let revised = "";
    try {
      await api.readStream(
        "/cowrite/revise/stream",
        { feedback: prevFeedback, history: draftHistory },
        (chunk) => {
          revised += chunk;
          setDraftText(revised);
        },
        ctrl.signal
      );
      setDraftHistory([
        ...draftHistory,
        { role: "user", content: prevFeedback },
        { role: "assistant", content: revised },
      ]);
      setPhase("draft_ready");
    } catch (e) {
      if ((e as Error).name !== "AbortError") setPhase("draft_ready");
    }
  }

  async function handleJudge() {
    setJudging(true);
    try {
      const result = await api.judgeContent(topic, draftText, related);
      setJudgeResult(result);
    } finally {
      setJudging(false);
    }
  }

  async function handleFinalize() {
    setFinalizing(true);
    try {
      const result = await api.finalizeContent(
        draftText,
        topic,
        [],
        initialSelectedIds
      );
      onFinalize(result.content_id);
      setPhase("done");
    } finally {
      setFinalizing(false);
    }
  }

  // ── Phase: topic ────────────────────────────────────────────
  if (phase === "topic") {
    return (
      <div className="space-y-5 max-w-2xl mx-auto">
        <div>
          <h2 className="font-semibold text-base mb-3">주제 설정</h2>
          <div className="flex gap-2">
            <Input
              placeholder="어떤 주제로 글을 쓸까요?"
              value={topic}
              onChange={e => setTopic(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSearch()}
              className="flex-1"
            />
            <Button
              onClick={handleSearch}
              disabled={searching || !topic.trim()}
              variant="outline"
            >
              {searching ? "검색 중..." : "글감 검색"}
            </Button>
          </div>
          {initialSelectedIds.length > 0 && (
            <p className="text-xs text-muted-foreground mt-2">
              선택한 글감 {initialSelectedIds.length}개가 글쓰기에 연결됩니다.
            </p>
          )}
        </div>

        {related.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              관련 글감 {related.length}개
            </p>
            {related.map(item => (
              <div
                key={item.id}
                className="rounded-lg border border-border bg-muted/30 p-3"
              >
                <p className="text-xs font-medium mb-1">
                  {item.title || "(제목 없음)"}
                </p>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  {item.text}
                </p>
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setPhase("discussing")}
            disabled={!topic.trim()}
          >
            AI와 토의하며 탐색
          </Button>
          <Button onClick={handleDraft} disabled={!topic.trim()}>
            바로 초안 작성
          </Button>
        </div>
      </div>
    );
  }

  // ── Phase: discussing ────────────────────────────────────────
  if (phase === "discussing") {
    return (
      <div className="flex flex-col max-w-2xl mx-auto" style={{ height: "calc(100vh - 160px)" }}>
        <div className="flex items-center justify-between mb-4 shrink-0">
          <div>
            <h2 className="font-semibold text-sm">주제 탐색</h2>
            <p className="text-xs text-muted-foreground">{topic}</p>
          </div>
          <Button size="sm" onClick={handleDraft}>
            초안 작성 →
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-1">
          {discussHistory.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-10">
              AI와 함께 주제를 탐색해보세요.
              <br />
              어떤 경험이나 생각이 있나요?
            </p>
          )}
          {discussHistory.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground rounded-br-sm"
                    : "bg-muted text-foreground rounded-bl-sm"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          {streamText && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-2xl rounded-bl-sm px-4 py-2.5 text-sm leading-relaxed bg-muted whitespace-pre-wrap">
                {streamText}
                <span className="inline-block w-1.5 h-3.5 bg-muted-foreground/60 ml-0.5 animate-pulse rounded-sm" />
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="flex gap-2 shrink-0">
          <Input
            placeholder="메시지 입력... (Enter로 전송)"
            value={discussInput}
            onChange={e => setDiscussInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleDiscuss();
              }
            }}
            disabled={streaming}
          />
          <Button
            onClick={handleDiscuss}
            disabled={streaming || !discussInput.trim()}
          >
            {streaming ? "..." : "전송"}
          </Button>
        </div>
      </div>
    );
  }

  // ── Phase: drafting / revising ───────────────────────────────
  if (phase === "drafting" || phase === "revising") {
    return (
      <div className="max-w-2xl mx-auto space-y-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <svg className="size-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          {phase === "drafting" ? "초안 작성 중..." : "퇴고 중..."}
        </div>
        {draftText && (
          <div className="rounded-lg border border-border bg-muted/20 p-4 text-sm whitespace-pre-wrap leading-relaxed">
            {draftText}
            <span className="inline-block w-1.5 h-3.5 bg-muted-foreground/60 ml-0.5 animate-pulse rounded-sm" />
          </div>
        )}
      </div>
    );
  }

  // ── Phase: draft_ready ───────────────────────────────────────
  if (phase === "draft_ready") {
    return (
      <div className="max-w-2xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-sm">초안 — {topic}</h2>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleJudge}
              disabled={judging}
            >
              {judging ? "평가 중..." : "품질 평가"}
            </Button>
            <Button
              size="sm"
              onClick={handleFinalize}
              disabled={finalizing}
            >
              {finalizing ? "저장 중..." : "원본 확정"}
            </Button>
          </div>
        </div>

        <Textarea
          value={draftText}
          onChange={e => setDraftText(e.target.value)}
          className="min-h-72 font-mono text-sm leading-relaxed"
        />

        {judgeResult && (
          <div
            className={`rounded-lg border p-4 text-sm space-y-2 ${
              judgeResult.passed
                ? "border-emerald-500/30 bg-emerald-500/10"
                : "border-amber-500/30 bg-amber-500/10"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">
                {judgeResult.passed ? "✓ 품질 기준 통과" : "△ 개선 권장"}
              </span>
              <div className="flex gap-1.5">
                {Object.entries(judgeResult.scores).map(([k, v]) => (
                  <span
                    key={k}
                    className="text-xs bg-black/10 dark:bg-white/10 rounded px-1.5 py-0.5"
                  >
                    {k}: {v}
                  </span>
                ))}
              </div>
            </div>
            <p className="text-muted-foreground text-xs leading-relaxed">
              {judgeResult.feedback}
            </p>
          </div>
        )}

        <div className="flex gap-2">
          <Input
            placeholder="퇴고 요청 (예: 더 간결하게, 감성적인 톤으로...)"
            value={feedback}
            onChange={e => setFeedback(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleRevise()}
          />
          <Button
            variant="outline"
            onClick={handleRevise}
            disabled={!feedback.trim()}
          >
            퇴고
          </Button>
        </div>
      </div>
    );
  }

  // ── Phase: done ──────────────────────────────────────────────
  if (phase === "done") {
    return (
      <div className="max-w-2xl mx-auto text-center py-20 space-y-3">
        <div className="text-5xl">✓</div>
        <h2 className="font-semibold text-lg">원본이 확정되었습니다</h2>
        <p className="text-sm text-muted-foreground">
          발행 탭에서 플랫폼별로 변환하고 발행하세요.
        </p>
      </div>
    );
  }

  return null;
}
