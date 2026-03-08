const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

// ---- User registration ----

export async function registerNickname(nickname: string): Promise<{ status?: string; error?: string; exists?: boolean }> {
  const res = await fetch(`${API_BASE}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nickname }),
  });
  return res.json();
}

export async function checkNickname(nickname: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/check-nickname?nickname=${encodeURIComponent(nickname)}`);
  const data = await res.json();
  return data.exists;
}

// ---- File upload ----

export interface UploadProgress {
  stage: string;
  message: string;
  current: number;
  total: number;
}

export async function uploadFile(
  file: File,
  nickname: string,
  onProgress?: (p: UploadProgress) => void,
) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("nickname", nickname);

  const res = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "上传失败");
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("无法读取响应流");

  const decoder = new TextDecoder();
  let buffer = "";
  let result = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.type === "progress") {
            onProgress?.(data);
          } else if (data.type === "done") {
            result = data;
          }
        } catch {
          // ignore
        }
      }
    }
  }

  if (!result) throw new Error("上传未完成");
  return result;
}

// ---- Chat ----

export async function sendMessage(
  message: string,
  nickname: string,
  onChunk: (text: string) => void,
  onDone: (messageId: number | null, sourceTypes?: string) => void,
  onStatus?: (status: string) => void,
) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, nickname }),
  });

  if (!res.ok) {
    throw new Error("请求失败");
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("无法读取响应流");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let currentEvent = "";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7);
      } else if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (currentEvent === "status") {
          onStatus?.(data);
          currentEvent = "";
        } else if (currentEvent === "done") {
          try {
            const parsed = JSON.parse(data);
            onDone(parsed.message_id ?? null, parsed.source_types ?? "");
          } catch {
            onDone(null);
          }
          return;
        } else if (data === "[DONE]") {
          onDone(null);
          return;
        } else {
          try {
            onChunk(JSON.parse(data));
          } catch {
            onChunk(data);
          }
        }
        currentEvent = "";
      }
    }
  }

  onDone(null);
}

export async function submitFeedback(
  messageId: number,
  rating: "accurate" | "inaccurate",
  nickname: string = "",
  sourceTypes: string = "",
): Promise<void> {
  await fetch(`${API_BASE}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message_id: messageId, rating, nickname, source_types: sourceTypes }),
  });
}

// ---- Analytics ----

export interface AnalyticsData {
  total: number;
  accurate: number;
  inaccurate: number;
  rate: number;
  trend: { date: string; accurate: number; inaccurate: number }[];
  by_version: { version: string; accurate: number; inaccurate: number }[];
  by_user: { user: string; accurate: number; inaccurate: number }[];
  recent: {
    id: number;
    message_id: number;
    user_id: string;
    rating: string;
    app_version: string;
    source_types: string;
    created_at: string;
  }[];
}

export async function getAnalytics(days: number = 30): Promise<AnalyticsData> {
  const res = await fetch(`${API_BASE}/analytics?days=${days}`);
  return res.json();
}

// ---- Messages & Documents ----

export async function getMessages(nickname: string): Promise<
  { role: string; content: string; created_at: string }[]
> {
  const res = await fetch(`${API_BASE}/messages?nickname=${encodeURIComponent(nickname)}`);
  const data = await res.json();
  return data.messages || [];
}

export interface DocumentInfo {
  doc_id: string;
  source_type: string;
  source_name: string;
  chunk_count: number;
  time_range_start: string | null;
  time_range_end: string | null;
  created_at: string;
}

export async function getDocuments(nickname: string): Promise<DocumentInfo[]> {
  const res = await fetch(`${API_BASE}/documents?nickname=${encodeURIComponent(nickname)}`);
  const data = await res.json();
  return data.documents || [];
}

export async function resetAll(nickname: string): Promise<void> {
  const res = await fetch(`${API_BASE}/reset?nickname=${encodeURIComponent(nickname)}`, { method: "DELETE" });
  if (!res.ok) throw new Error("清除失败");
}
