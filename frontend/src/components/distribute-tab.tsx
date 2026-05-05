"use client";

import { useState } from "react";
import * as api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type Platform = "instagram" | "brunch" | "thread";

const cleanTag = (tag: string) => tag.replace(/^#+/, "");

const PLATFORMS: { id: Platform; name: string; desc: string }[] = [
  { id: "instagram", name: "Instagram", desc: "캡션 + 해시태그" },
  { id: "brunch",    name: "브런치",    desc: "서사형 아티클" },
  { id: "thread",    name: "스레드",    desc: "3~5개 분절 포스트" },
];

interface Props {
  contentId: string | null;
}

export default function DistributeTab({ contentId }: Props) {
  const [selected, setSelected] = useState<Set<Platform>>(new Set());
  const [converting, setConverting] = useState(false);
  const [result, setResult] = useState<api.ConvertResult | null>(null);
  const [imageUrl, setImageUrl] = useState("");
  const [imagePrompt, setImagePrompt] = useState("");
  const [generatingImage, setGeneratingImage] = useState(false);
  const [publishing, setPublishing] = useState<Platform | null>(null);
  const [saved, setSaved] = useState<Set<Platform>>(new Set());
  const [publishedUrls, setPublishedUrls] = useState<Record<string, string | null>>({});

  if (!contentId) {
    return (
      <div className="text-center py-20 text-muted-foreground text-sm space-y-2">
        <p className="text-2xl">✍️</p>
        <p>글쓰기 탭에서 원본을 확정한 뒤 여기로 이동하세요.</p>
      </div>
    );
  }

  function togglePlatform(p: Platform) {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(p)) next.delete(p);
      else next.add(p);
      return next;
    });
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

  function handleReset() {
    setResult(null);
    setSaved(new Set());
    setPublishedUrls({});
    setImageUrl("");
    setImagePrompt("");
  }

  async function handleGenerateImage() {
    if (!result) return;
    setGeneratingImage(true);
    try {
      const res = await api.generateImagePrompt(
        result.instagram.caption,
        result.instagram.hashtags
      );
      setImagePrompt(res.prompt);
      setImageUrl(res.image_url);
    } finally {
      setGeneratingImage(false);
    }
  }

  async function handlePublishInstagram() {
    if (!result) return;
    setPublishing("instagram");
    try {
      const res = await api.publishInstagram(
        contentId!,
        result.instagram.caption,
        result.instagram.hashtags.map(cleanTag),
        imageUrl
      ) as { published_url?: string | null };
      setSaved(prev => new Set([...prev, "instagram"]));
      setPublishedUrls(prev => ({ ...prev, instagram: res.published_url ?? null }));
    } finally {
      setPublishing(null);
    }
  }

  async function handlePublishBrunch() {
    if (!result) return;
    setPublishing("brunch");
    try {
      const res = await api.publishBrunch(contentId!, result.brunch.title, result.brunch.body) as { published_url?: string | null };
      setSaved(prev => new Set([...prev, "brunch"]));
      setPublishedUrls(prev => ({ ...prev, brunch: res.published_url ?? null }));
    } finally {
      setPublishing(null);
    }
  }

  async function handlePublishThread() {
    if (!result) return;
    setPublishing("thread");
    try {
      const res = await api.publishThread(contentId!, result.thread.posts) as { published_url?: string | null };
      setSaved(prev => new Set([...prev, "thread"]));
      setPublishedUrls(prev => ({ ...prev, thread: res.published_url ?? null }));
    } finally {
      setPublishing(null);
    }
  }

  // ── 플랫폼 선택 화면 ──────────────────────────────────────────
  if (!result) {
    return (
      <div className="max-w-xl mx-auto space-y-6">
        <div>
          <h2 className="font-semibold text-base mb-1">발행 플랫폼 선택</h2>
          <p className="text-xs text-muted-foreground">변환할 플랫폼을 선택하세요.</p>
        </div>

        <div className="space-y-2">
          {PLATFORMS.map(p => (
            <button
              key={p.id}
              onClick={() => togglePlatform(p.id)}
              className={`w-full text-left rounded-xl border p-4 transition-all ${
                selected.has(p.id)
                  ? "border-primary bg-primary/5 ring-1 ring-primary"
                  : "border-border hover:border-muted-foreground/40 hover:bg-muted/30"
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">{p.name}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{p.desc}</p>
                </div>
                <div
                  className={`size-4 rounded-full border-2 transition-colors ${
                    selected.has(p.id)
                      ? "border-primary bg-primary"
                      : "border-muted-foreground/40"
                  }`}
                />
              </div>
            </button>
          ))}
        </div>

        <Button
          className="w-full"
          onClick={handleConvert}
          disabled={selected.size === 0 || converting}
        >
          {converting ? (
            <span className="flex items-center gap-2">
              <svg className="size-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              변환 중...
            </span>
          ) : (
            `${selected.size > 0 ? [...selected].map(p => PLATFORMS.find(pl => pl.id === p)?.name).join(" · ") : "플랫폼을 선택하세요"} 변환`
          )}
        </Button>
      </div>
    );
  }

  // ── 변환 결과 화면 ────────────────────────────────────────────
  const threadPosts = result.thread.posts ?? [];

  return (
    <div className="space-y-4 max-w-3xl mx-auto">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-sm">변환 결과</h2>
        <Button variant="outline" size="sm" onClick={handleReset}>
          다시 선택
        </Button>
      </div>

      {selected.has("instagram") && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-sm">
              <span>Instagram</span>
              {saved.has("instagram") ? (
                <div className="flex items-center gap-2">
                  <Badge className="text-xs bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                    발행됨
                  </Badge>
                  {publishedUrls.instagram && (
                    <a
                      href={publishedUrls.instagram}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-primary underline underline-offset-2"
                    >
                      게시물 보기 →
                    </a>
                  )}
                </div>
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
              {result.instagram.caption}
            </p>
            {result.instagram.hashtags.length > 0 && (
              <div className="flex gap-1.5 flex-wrap">
                {result.instagram.hashtags.map(tag => (
                  <span key={tag} className="text-xs text-primary/80">#{cleanTag(tag)}</span>
                ))}
              </div>
            )}
            {!saved.has("instagram") && (
              <div className="space-y-2">
                <div className="flex gap-2">
                  <Input
                    placeholder="이미지 URL (발행에 필요)"
                    value={imageUrl}
                    onChange={e => setImageUrl(e.target.value)}
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleGenerateImage}
                    disabled={generatingImage}
                    className="shrink-0"
                  >
                    {generatingImage ? (
                      <span className="flex items-center gap-1.5">
                        <svg className="size-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                        </svg>
                        생성 중...
                      </span>
                    ) : "AI 이미지 생성"}
                  </Button>
                </div>
                {imageUrl && (
                  <div className="space-y-1.5">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={imageUrl}
                      alt="생성된 이미지"
                      className="w-full rounded-lg object-cover aspect-square"
                      onError={() => setImageUrl("")}
                    />
                    {imagePrompt && (
                      <p className="text-xs text-muted-foreground">
                        프롬프트: {imagePrompt}
                      </p>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleGenerateImage}
                      disabled={generatingImage}
                    >
                      재생성
                    </Button>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {selected.has("brunch") && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-sm">
              <span>브런치</span>
              {saved.has("brunch") ? (
                <div className="flex items-center gap-2">
                  <Badge className="text-xs bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                    저장됨
                  </Badge>
                  {publishedUrls.brunch && (
                    <a href={publishedUrls.brunch} target="_blank" rel="noopener noreferrer"
                      className="text-xs text-primary underline underline-offset-2">
                      게시물 보기 →
                    </a>
                  )}
                </div>
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
            {result.brunch.title && (
              <p className="text-sm font-medium mb-2">{result.brunch.title}</p>
            )}
            <p className="text-sm whitespace-pre-wrap leading-relaxed line-clamp-8">
              {result.brunch.body}
            </p>
          </CardContent>
        </Card>
      )}

      {selected.has("thread") && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-sm">
              <span>스레드</span>
              {saved.has("thread") ? (
                <div className="flex items-center gap-2">
                  <Badge className="text-xs bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                    저장됨
                  </Badge>
                  {publishedUrls.thread && (
                    <a href={publishedUrls.thread} target="_blank" rel="noopener noreferrer"
                      className="text-xs text-primary underline underline-offset-2">
                      게시물 보기 →
                    </a>
                  )}
                </div>
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
      )}
    </div>
  );
}
