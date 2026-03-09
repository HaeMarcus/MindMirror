"use client";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  nickname?: string;
  isStreaming?: boolean;
  feedbackGiven?: "accurate" | "inaccurate" | null;
  onFeedback?: (rating: "accurate" | "inaccurate") => void;
}

const SECTION_LABELS = [
  { key: "核心洞察", color: "text-rose-600", bg: "bg-rose-50/80", border: "border-rose-100", icon: "◆" },
  { key: "模式识别", color: "text-violet-600", bg: "bg-violet-50/80", border: "border-violet-100", icon: "◇" },
  { key: "证据归因", color: "text-blue-600", bg: "bg-blue-50/80", border: "border-blue-100", icon: "△" },
];

function stripMarkdown(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^[-*]\s+/gm, "");
}

function parseInsightSections(content: string) {
  const sections: { label: string; content: string; color: string; bg: string; border: string; icon: string }[] = [];
  let preamble = "";

  let firstMarkerIdx = -1;
  for (const sec of SECTION_LABELS) {
    const idx = content.indexOf(`【${sec.key}】`);
    if (idx !== -1 && (firstMarkerIdx === -1 || idx < firstMarkerIdx)) {
      firstMarkerIdx = idx;
    }
  }
  if (firstMarkerIdx > 0) {
    preamble = content.slice(0, firstMarkerIdx).trim();
  }

  for (const sec of SECTION_LABELS) {
    const marker = `【${sec.key}】`;
    const idx = content.indexOf(marker);
    if (idx === -1) continue;

    const afterMarker = content.slice(idx + marker.length);
    const nextIdx = afterMarker.search(/【[^【】]+】/);
    const sectionContent = nextIdx >= 0 ? afterMarker.slice(0, nextIdx) : afterMarker;

    sections.push({
      label: sec.key,
      content: sectionContent.trim(),
      color: sec.color,
      bg: sec.bg,
      border: sec.border,
      icon: sec.icon,
    });
  }

  return { sections, preamble };
}

function ClaudeAvatar() {
  return (
    <img
      src="/claude-icon.svg"
      alt="Claude"
      className="w-6 h-6 flex-shrink-0 mt-1"
    />
  );
}

function FeedbackButtons({
  feedbackGiven,
  onFeedback,
}: {
  feedbackGiven?: "accurate" | "inaccurate" | null;
  onFeedback?: (rating: "accurate" | "inaccurate") => void;
}) {
  if (!onFeedback) return null;

  return (
    <div className="flex gap-2 mt-2 ml-8">
      <button
        onClick={() => onFeedback("accurate")}
        disabled={!!feedbackGiven}
        className={`flex items-center gap-1 px-2.5 py-1 text-xs rounded-full transition-all duration-200 ${
          feedbackGiven === "accurate"
            ? "bg-green-100 text-green-700 scale-105"
            : feedbackGiven
              ? "opacity-30 text-gray-400 cursor-not-allowed"
              : "text-gray-400 hover:bg-green-50 hover:text-green-600 hover:scale-105"
        }`}
      >
        <span>👍</span>
        <span>很准确</span>
      </button>
      <button
        onClick={() => onFeedback("inaccurate")}
        disabled={!!feedbackGiven}
        className={`flex items-center gap-1 px-2.5 py-1 text-xs rounded-full transition-all duration-200 ${
          feedbackGiven === "inaccurate"
            ? "bg-red-100 text-red-700 scale-105"
            : feedbackGiven
              ? "opacity-30 text-gray-400 cursor-not-allowed"
              : "text-gray-400 hover:bg-red-50 hover:text-red-600 hover:scale-105"
        }`}
      >
        <span>👎</span>
        <span>不准确</span>
      </button>
    </div>
  );
}

export default function MessageBubble({ role, content, isStreaming, feedbackGiven, onFeedback }: MessageBubbleProps) {
  if (role === "user") {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[75%] lg:max-w-[65%] rounded-2xl rounded-br-md bg-[#8a9a7e] text-white px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap shadow-sm">
          {content}
        </div>
      </div>
    );
  }

  const { sections, preamble } = parseInsightSections(content);

  if (sections.length >= 1) {
    return (
      <div className="mb-4">
        <div className="flex justify-start items-start gap-2">
          <ClaudeAvatar />
          <div className="max-w-[82%] lg:max-w-[75%]">
            {preamble && (
              <div className="rounded-2xl rounded-bl-md bg-white/80 backdrop-blur-sm border border-gray-200/60 px-4 py-3 text-sm text-gray-800 leading-relaxed whitespace-pre-wrap shadow-sm mb-3">
                {stripMarkdown(preamble)}
              </div>
            )}
            <div className="space-y-2.5 animate-card-stagger">
              {sections.map((sec) => (
                <div key={sec.label} className={`${sec.bg} backdrop-blur-sm ${sec.border} border rounded-xl px-4 py-3 shadow-sm animate-fade-in`}>
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
        </div>
        {!isStreaming && <FeedbackButtons feedbackGiven={feedbackGiven} onFeedback={onFeedback} />}
      </div>
    );
  }

  return (
    <div className="mb-4">
      <div className="flex justify-start items-start gap-2">
        <ClaudeAvatar />
        <div className="max-w-[82%]">
          <div className="rounded-2xl rounded-bl-md bg-white/80 backdrop-blur-sm border border-gray-200/60 px-4 py-3 text-sm text-gray-800 leading-relaxed whitespace-pre-wrap shadow-sm">
            {stripMarkdown(content)}
          </div>
        </div>
      </div>
      {!isStreaming && <FeedbackButtons feedbackGiven={feedbackGiven} onFeedback={onFeedback} />}
    </div>
  );
}
