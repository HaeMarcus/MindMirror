const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export interface UploadProgress {
  stage: string;
  message: string;
  current: number;
  total: number;
}

export async function uploadFile(
  file: File,
  onProgress?: (p: UploadProgress) => void,
) {
  const formData = new FormData();
  formData.append("file", file);

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

export async function sendMessage(
  message: string,
  onChunk: (text: string) => void,
  onDone: (messageId: number | null) => void,
  onStatus?: (status: string) => void,
) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
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
            onDone(parsed.message_id ?? null);
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

export async function submitFeedback(messageId: number, rating: "accurate" | "inaccurate"): Promise<void> {
  await fetch(`${API_BASE}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message_id: messageId, rating }),
  });
}

export async function getMessages(): Promise<
  { role: string; content: string; created_at: string }[]
> {
  const res = await fetch(`${API_BASE}/messages`);
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

export async function getDocuments(): Promise<DocumentInfo[]> {
  const res = await fetch(`${API_BASE}/documents`);
  const data = await res.json();
  return data.documents || [];
}

export async function resetAll(): Promise<void> {
  const res = await fetch(`${API_BASE}/reset`, { method: "DELETE" });
  if (!res.ok) throw new Error("清除失败");
}
