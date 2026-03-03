"use client";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
}

const SECTION_LABELS = [
  { key: "核心洞察", color: "text-rose-600", bg: "bg-rose-50", icon: "◆" },
  { key: "证据归因", color: "text-blue-600", bg: "bg-blue-50", icon: "◇" },
  { key: "防御机制", color: "text-amber-600", bg: "bg-amber-50", icon: "△" },
  { key: "实验性下一步", color: "text-emerald-600", bg: "bg-emerald-50", icon: "▷" },
];

function stripMarkdown(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^[-*]\s+/gm, "");
}

function parseInsightSections(content: string) {
  const sections: { label: string; content: string; color: string; bg: string; icon: string }[] = [];
  let remaining = content;

  for (const sec of SECTION_LABELS) {
    const marker = `【${sec.key}】`;
    const idx = remaining.indexOf(marker);
    if (idx === -1) continue;

    // Find end: either next 【 or end of string
    const afterMarker = remaining.slice(idx + marker.length);
    const nextIdx = afterMarker.search(/【[^【】]+】/);
    const sectionContent = nextIdx >= 0 ? afterMarker.slice(0, nextIdx) : afterMarker;

    sections.push({
      label: sec.key,
      content: sectionContent.trim(),
      color: sec.color,
      bg: sec.bg,
      icon: sec.icon,
    });
  }

  return sections;
}

export default function MessageBubble({ role, content }: MessageBubbleProps) {
  if (role === "user") {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[75%] rounded-2xl rounded-br-md bg-[#8a9a7e] text-white px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap">
          {content}
        </div>
      </div>
    );
  }

  // Assistant: try to parse structured output
  const sections = parseInsightSections(content);

  if (sections.length >= 2) {
    return (
      <div className="flex justify-start mb-4">
        <div className="max-w-[85%] space-y-3">
          {sections.map((sec, i) => (
            <div key={i} className={`${sec.bg} rounded-xl px-4 py-3`}>
              <div className={`text-xs font-semibold ${sec.color} mb-1.5 flex items-center gap-1`}>
                <span>{sec.icon}</span>
                <span>{sec.label}</span>
              </div>
              <div className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                {stripMarkdown(sec.content)}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Fallback: plain text
  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[85%] rounded-2xl rounded-bl-md bg-white border border-gray-200 px-4 py-3 text-sm text-gray-800 leading-relaxed whitespace-pre-wrap shadow-sm">
        {stripMarkdown(content)}
      </div>
    </div>
  );
}
