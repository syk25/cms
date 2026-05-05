const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Source = "NOTION" | "MANUAL";

export interface RawContent {
  id: string;
  title: string;
  text: string;
  source: Source;
  category: string;
  tags: string[];
  is_used: boolean;
  created_at: string;
}

export interface ConvertResult {
  content_id: string;
  instagram: { caption: string; hashtags: string[] };
  brunch: { title: string; body: string };
  thread: { posts: string[] };
}

export interface JudgeResult {
  scores: Record<string, number>;
  feedback: string;
  passed: boolean;
}

export type SyncEventType = "start" | "pages_fetched" | "progress" | "done" | "error";

export interface SyncEvent {
  type: SyncEventType;
  total_before?: number;
  total?: number;
  processed?: number;  // progress 이벤트
  fetched?: number;    // done 이벤트
  imported?: number;
  skipped?: number;
  message?: string;
}

async function post<T>(path: string, body?: object): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export async function getContents(
  limit = 20,
  offset = 0,
  keyword = "",
  isUsed: "all" | "used" | "unused" = "all"
) {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (keyword) params.set("search", keyword);
  if (isUsed === "used") params.set("is_used", "true");
  if (isUsed === "unused") params.set("is_used", "false");
  const res = await fetch(`${API}/ingest/contents?${params}`);
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json() as Promise<{ total: number; items: RawContent[] }>;
}

export async function clearContents() {
  const res = await fetch(`${API}/ingest/contents`, { method: "DELETE" });
  return res.json();
}

export function syncNotion(onEvent: (e: SyncEvent) => void): AbortController {
  const ctrl = new AbortController();
  (async () => {
    try {
      const res = await fetch(`${API}/ingest/notion/stream`, {
        method: "POST",
        signal: ctrl.signal,
      });
      const reader = res.body!.getReader();
      const dec = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop() ?? "";
        for (const line of lines) {
          if (line.trim()) {
            try { onEvent(JSON.parse(line)); } catch {}
          }
        }
      }
    } catch (e) {
      if ((e as Error).name !== "AbortError") {
        onEvent({ type: "error", message: String(e) });
      }
    }
  })();
  return ctrl;
}

export async function searchContents(query: string, n_results = 5) {
  return post<{ results: RawContent[] }>("/discovery/search", { query, n_results });
}

export async function readStream(
  path: string,
  body: object,
  onChunk: (text: string) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.body) return;
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onChunk(dec.decode(value));
  }
}

export async function judgeContent(
  topic: string,
  draft: string,
  related_contents: object[]
) {
  return post<JudgeResult>("/cowrite/judge", { topic, draft, related_contents });
}

export async function finalizeContent(
  text: string,
  topic: string,
  tags: string[],
  raw_content_ids: string[]
) {
  return post<{ content_id: string; embedding_id: string }>("/cowrite/finalize", {
    text,
    topic,
    tags,
    raw_content_ids,
  });
}

export async function generateImagePrompt(caption: string, hashtags: string[]) {
  return post<{ prompt: string; image_url: string }>("/distribute/image-prompt", {
    caption,
    hashtags,
  });
}

export async function convertContent(content_id: string) {
  return post<ConvertResult>("/distribute/convert", { content_id });
}

export async function publishInstagram(
  content_id: string,
  caption: string,
  hashtags: string[],
  image_url: string
) {
  return post("/distribute/publish/instagram", { content_id, caption, hashtags, image_url });
}

export async function publishBrunch(content_id: string, title: string, body: string) {
  return post("/distribute/publish/brunch", { content_id, title, body });
}

export async function publishThread(content_id: string, posts: string[]) {
  return post("/distribute/publish/thread", { content_id, posts });
}
