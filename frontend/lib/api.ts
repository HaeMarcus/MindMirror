const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export async function uploadFile(file: File) {
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

  return res.json();
}

export async function sendMessage(
  message: string,
  onChunk: (text: string) => void,
  onDone: () => void,
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
        } else if (data === "[DONE]") {
          onDone();
          return;
        } else {
          onChunk(data);
        }
        currentEvent = "";
      }
    }
  }

  onDone();
}

export async function getMessages(): Promise<
  { role: string; content: string; created_at: string }[]
> {
  const res = await fetch(`${API_BASE}/messages`);
  const data = await res.json();
  return data.messages || [];
}
