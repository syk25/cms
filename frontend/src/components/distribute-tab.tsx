"use client";

import { useState } from "react";
import * as api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  contentId: string | null;
}

export default function DistributeTab({ contentId }: Props) {
  const [converting, setConverting] = useState(false);
  const [result, setResult] = useState<api.ConvertResult | null>(null);
  const [imageUrl, setImageUrl] = useState("");
  const [publishing, setPublishing] = useState<string | null>(null);
  const [saved, setSaved] = useState<Set<string>>(new Set());

  if (!contentId) {
    return (
      <div className="text-center py-20 text-muted-foreground text-sm space-y-2">
        <p className="text-2xl">✍️</p>
        <p>글쓰기 탭에서 원본을 확정한 뒤 여기로 이동하세요.</p>
      </div>
    );
  }

  async function handleConvert() {
    setConverting(true);
    setResult(null);
    setSaved(new Set());
    try {
      const res = await api.convertContent(contentId!);
      setResult(res);
    } catch (e) {
      alert(`변환 실패: ${String(e)}`);
    } finally {
      setConverting(false);
    }
  }

  async function handlePublishInstagram() {
    if (!result) return;
    setPublishing("instagram");
    try {
      await api.publishInstagram(
        contentId!,
        result.instagram.body,
        result.instagram.hashtags,
        imageUrl
      );
      setSaved(prev => new Set([...prev, "instagram"]));
    } finally {
      setPublishing(null);
    }
  }

  async function handlePublishBrunch() {
    if (!result) return;
    setPublishing("brunch");
    try {
      const lines = result.brunch.body.split("\n");
      const title = lines[0].replace(/^#+\s*/, "") || "제목 없음";
      const body = lines.slice(1).join("\n").trim();
      await api.publishBrunch(contentId!, title, body);
      setSaved(prev => new Set([...prev, "brunch"]));
    } finally {
      setPublishing(null);
    }
  }

  async function handlePublishThread() {
    if (!result) return;
    setPublishing("thread");
    try {
      const posts = Array.isArray(result.thread.body)
        ? result.thread.body
        : [result.thread.body];
      await api.publishThread(contentId!, posts);
      setSaved(prev => new Set([...prev, "thread"]));
    } finally {
      setPublishing(null);
    }
  }

  if (!result) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <Button size="lg" onClick={handleConvert} disabled={converting}>
          {converting ? (
            <span className="flex items-center gap-2">
              <svg className="size-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              변환 중...
            </span>
          ) : (
            "3개 플랫폼 동시 변환"
          )}
        </Button>
        <p className="text-xs text-muted-foreground">
          Instagram · 브런치 · 스레드 형식으로 동시 변환합니다
        </p>
      </div>
    );
  }

  const threadPosts = Array.isArray(result.thread.body)
    ? result.thread.body
    : [result.thread.body];

  return (
    <div className="space-y-4 max-w-3xl mx-auto">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-sm">변환 결과</h2>
        <Button variant="outline" size="sm" onClick={handleConvert} disabled={converting}>
          재변환
        </Button>
      </div>

      {/* Instagram */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-sm">
            <span>Instagram</span>
            {saved.has("instagram") ? (
              <Badge className="text-xs bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                발행됨
              </Badge>
            ) : (
              <Button
                size="sm"
                onClick={handlePublishInstagram}
                disabled={publishing === "instagram" || !imageUrl.trim()}
              >
                {publishing === "instagram" ? "발행 중..." : "발행"}
              </Button>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm whitespace-pre-wrap leading-relaxed">
            {result.instagram.body}
          </p>
          {result.instagram.hashtags.length > 0 && (
            <div className="flex gap-1.5 flex-wrap">
              {result.instagram.hashtags.map(tag => (
                <span key={tag} className="text-xs text-primary/80">
                  #{tag}
                </span>
              ))}
            </div>
          )}
          {!saved.has("instagram") && (
            <Input
              placeholder="이미지 URL (발행에 필요)"
              value={imageUrl}
              onChange={e => setImageUrl(e.target.value)}
            />
          )}
        </CardContent>
      </Card>

      {/* Brunch */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-sm">
            <span>브런치</span>
            {saved.has("brunch") ? (
              <Badge className="text-xs bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                저장됨
              </Badge>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={handlePublishBrunch}
                disabled={publishing === "brunch"}
              >
                {publishing === "brunch" ? "저장 중..." : "저장"}
              </Button>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm whitespace-pre-wrap leading-relaxed line-clamp-8">
            {result.brunch.body}
          </p>
        </CardContent>
      </Card>

      {/* Thread */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-sm">
            <span>스레드</span>
            {saved.has("thread") ? (
              <Badge className="text-xs bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                저장됨
              </Badge>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={handlePublishThread}
                disabled={publishing === "thread"}
              >
                {publishing === "thread" ? "저장 중..." : "저장"}
              </Button>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {threadPosts.map((post, i) => (
              <div
                key={i}
                className="rounded-lg border border-border bg-muted/30 p-3 text-sm leading-relaxed"
              >
                <span className="text-xs text-muted-foreground mr-2 font-mono">
                  {i + 1}/{threadPosts.length}
                </span>
                {post}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
