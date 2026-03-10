"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import MessageBubble from "./MessageBubble";
import Sidebar from "./Sidebar";
import UploadPanel from "./UploadPanel";
import DataPanel from "./DataPanel";
import NicknamePrompt from "./NicknamePrompt";
import { sendMessage, getMessages, resetAll, submitFeedback } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  messageId?: number | null;
  feedbackGiven?: "accurate" | "inaccurate" | null;
  sourceTypes?: string;
  timestamp?: string;
}

const EMPTY_STATE_CARDS = [
  {
    icon: "👤",
    title: "大五人格与MBTI",
    desc: "从数据中分析你的人格特征",
    prompt: "请基于我各维度数据，从大五人格（开放性、尽责性、外向性、宜人性、神经质）的角度分析我的人格特征。并推断我的 MBTI 类型。",
  },
  {
    icon: "🔍",
    title: "言行一致性",
    desc: "发现你说的与做的之间的差异",
    prompt: "请基于我各维度数据，归纳我言语与行为的不一致之处。",
  },
  {
    icon: "💰",
    title: "消费观念洞察",
    desc: "分析你的消费习惯与价值观",
    prompt: "请基于我各维度数据，分析我的消费习惯和消费观念。",
  },
  {
    icon: "🧭",
    title: "自由提问",
    desc: "问任何关于你自己的问题",
    prompt: "",
  },
];

const QUICK_ACTIONS = [
  { label: "大五人格与MBTI", icon: "👤", prompt: "请基于我各维度数据，从大五人格（开放性、尽责性、外向性、宜人性、神经质）的角度分析我的人格特征。并推断我的 MBTI 类型。" },
  { label: "言行一致性洞察", icon: "🔍", prompt: "请基于我各维度数据，归纳我言语与行为的不一致之处。" },
  { label: "消费观念洞察", icon: "💰", prompt: "请基于我各维度数据，分析我的消费习惯和消费观念。" },
];

export default function ChatWindow() {
  const [nickname, setNickname] = useState<string | null>(null);
  const [showNicknamePrompt, setShowNicknamePrompt] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [showUpload, setShowUpload] = useState(false);
  const [showData, setShowData] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const streamBuffer = useRef("");
  const [streamingContent, setStreamingContent] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);

  // Initialize nickname from localStorage
  useEffect(() => {
    const stored = localStorage.getItem("mm_nickname");
    if (stored) {
      setNickname(stored);
    } else {
      setShowNicknamePrompt(true);
    }
    // Restore sidebar preference
    const sidebarPref = localStorage.getItem("mm_sidebar");
    if (sidebarPref === "closed") setSidebarOpen(false);
  }, []);

  // Persist sidebar state
  useEffect(() => {
    localStorage.setItem("mm_sidebar", sidebarOpen ? "open" : "closed");
  }, [sidebarOpen]);

  // Load history when nickname is set
  useEffect(() => {
    if (!nickname) return;
    getMessages(nickname)
      .then((msgs) => {
        if (msgs.length > 0) {
          setMessages(msgs.map((m) => ({ role: m.role as "user" | "assistant", content: m.content, timestamp: m.created_at })));
        }
      })
      .catch(() => {});
  }, [nickname]);

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isStreaming, streamingContent]);

  // Track scroll position for scroll-to-bottom button
  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
    setShowScrollBtn(!atBottom);
  }, []);

  const scrollToBottom = () => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  };

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 128) + "px";
  };

  const handleNicknameConfirm = (name: string) => {
    setNickname(name);
    setShowNicknamePrompt(false);
  };

  const handleSend = async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || isStreaming || !nickname) return;

    setInput("");
    if (inputRef.current) { inputRef.current.style.height = "auto"; }
    setMessages((prev) => [...prev, { role: "user", content: msg, timestamp: new Date().toISOString() }]);
    setIsStreaming(true);
    setStatusText("正在处理...");
    streamBuffer.current = "";

    try {
      await sendMessage(
        msg,
        nickname,
        (chunk) => {
          streamBuffer.current += chunk;
          setStreamingContent(streamBuffer.current);
          setStatusText("");
        },
        (messageId, sourceTypes) => {
          const fullContent = streamBuffer.current;
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: fullContent, messageId, feedbackGiven: null, sourceTypes, timestamp: new Date().toISOString() },
          ]);
          setIsStreaming(false);
          setStatusText("");
          setStreamingContent("");
        },
        (status) => {
          setStatusText(status);
        },
      );
    } catch {
      setIsStreaming(false);
      setStatusText("");
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "抱歉，请求出错了。请检查后端服务是否正常运行。" },
      ]);
    }
  };

  const handleFeedback = async (index: number, rating: "accurate" | "inaccurate") => {
    const msg = messages[index];
    if (!msg.messageId) return;
    setMessages((prev) =>
      prev.map((m, i) => (i === index ? { ...m, feedbackGiven: rating } : m))
    );
    try {
      await submitFeedback(msg.messageId, rating, nickname || "", msg.sourceTypes || "");
    } catch {
      // silently fail
    }
  };

  const handleReset = async () => {
    if (!nickname) return;
    if (!confirm("确定要清空所有数据并退出当前用户吗？（对话历史、上传的文件、记忆、用户记录都会被删除）")) return;
    try {
      await resetAll(nickname);
      localStorage.removeItem("mm_nickname");
      setNickname(null);
      setMessages([]);
      setShowNicknamePrompt(true);
    } catch {
      alert("清除失败，请稍后重试");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const hasMessages = messages.length > 0 || isStreaming;

  return (
    <div className="flex h-screen w-full bg-gradient-to-br from-[#f6f9f4] via-[#f0f4ee] to-[#eaf0e6]">
      {/* Nickname Prompt */}
      {showNicknamePrompt && <NicknamePrompt onConfirm={handleNicknameConfirm} />}

      {/* Sidebar */}
      {nickname && (
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          nickname={nickname}
          messageCount={messages.length}
          onOpenUpload={() => setShowUpload(true)}
          onOpenData={() => setShowData(true)}
          onReset={handleReset}
        />
      )}

      {/* Main chat area */}
      <main className="flex-1 flex flex-col min-w-0 relative">
        {/* Minimal header */}
        <header className="flex items-center h-14 px-5 border-b border-gray-200/60 bg-white/60 backdrop-blur-sm flex-shrink-0">
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-1.5 rounded-md hover:bg-gray-100 text-gray-500 mr-3 transition-colors"
              title="展开侧栏"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <line x1="9" y1="3" x2="9" y2="21" />
                <polyline points="13 8 16 12 13 16" />
              </svg>
            </button>
          )}
          <h1 className="text-base font-bold text-gray-800">MindMirror</h1>
          <span className="text-sm text-gray-400 ml-2">基于多维数据的 AI 自我觉察助手</span>
          <span className="ml-auto text-sm text-gray-400 font-medium">隐私持续守护中 🔒</span>
        </header>

        {/* Messages area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto relative" onScroll={handleScroll}>
          {!hasMessages ? (
            /* Empty state */
            <div className="flex flex-col items-center justify-center h-full px-4 animate-fade-in">
              <div className="max-w-2xl w-full text-center">
                <div className="text-6xl mb-4 animate-float">🪞</div>
                <h2 className="text-2xl font-bold text-gray-700 mb-2">
                  你好{nickname ? `，${nickname}` : ""}
                </h2>
                <p className="text-gray-400 mb-8">
                  导入你的数据，开始一场关于自己的对话
                </p>

                {/* Insight cards grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto stagger-grid">
                  {EMPTY_STATE_CARDS.map((card) => (
                    <button
                      key={card.title}
                      onClick={() => {
                        if (card.prompt) {
                          handleSend(card.prompt);
                        } else {
                          inputRef.current?.focus();
                        }
                      }}
                      disabled={isStreaming}
                      className="group text-left p-4 rounded-2xl bg-white/70 backdrop-blur-sm border border-gray-200/60 hover:border-[#8a9a7e]/40 hover:bg-white hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-40 animate-fade-in"
                    >
                      <span className="text-2xl block mb-2">{card.icon}</span>
                      <p className="text-sm font-medium text-gray-700 group-hover:text-[#6a7a5e] transition-colors">
                        {card.title}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">{card.desc}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* Chat messages */
            <div className="max-w-4xl mx-auto px-4 md:px-8 py-6">
              {messages.map((msg, i) => (
                <div key={i} className="animate-msg-in">
                  <MessageBubble
                    role={msg.role}
                    content={msg.content}
                    timestamp={msg.timestamp}
                    feedbackGiven={msg.feedbackGiven}
                    onFeedback={msg.role === "assistant" && msg.messageId ? (rating) => handleFeedback(i, rating) : undefined}
                  />
                </div>
              ))}
              {isStreaming && (
                <div className="animate-msg-in">
                  {streamingContent ? (
                    <MessageBubble role="assistant" content={streamingContent} isStreaming />
                  ) : (
                    <div className="flex justify-start mb-4 items-start gap-3">
                      <img src="/claude-icon.svg" alt="Claude" className="w-8 h-8 flex-shrink-0 mt-1" />
                      <div className="bg-white/80 backdrop-blur-sm border border-gray-200/60 rounded-2xl px-4 py-3 shadow-sm">
                        <div className="flex items-center gap-2">
                          <div className="flex gap-1">
                            <span className="w-1.5 h-1.5 bg-[#8a9a7e] rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                            <span className="w-1.5 h-1.5 bg-[#8a9a7e] rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                            <span className="w-1.5 h-1.5 bg-[#8a9a7e] rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                          </div>
                          {statusText && (
                            <span className="text-xs text-gray-400">{statusText}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Scroll to bottom button */}
        {showScrollBtn && hasMessages && (
          <button
            onClick={scrollToBottom}
            className="absolute bottom-28 right-6 z-10 p-2.5 rounded-full bg-white/90 backdrop-blur-sm border border-gray-200/60 shadow-lg text-gray-500 hover:text-gray-700 hover:shadow-xl transition-all duration-200 animate-scroll-btn"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>
        )}

        {/* Input area + Quick actions */}
        <div className="flex-shrink-0 px-4 md:px-8 pb-6 pt-2">
          <div className="max-w-4xl mx-auto">
            <div className="relative flex items-end bg-white/80 backdrop-blur-sm border border-gray-200/60 rounded-2xl shadow-sm focus-within:shadow-md focus-within:border-[#8a9a7e]/40 transition-all duration-200">
              {/* Upload button inside input */}
              <button
                onClick={() => setShowUpload(true)}
                className="flex-shrink-0 p-2.5 ml-1 text-gray-400 hover:text-[#7a8a6e] transition-colors"
                title="导入数据"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                </svg>
              </button>

              <textarea
                ref={inputRef}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="输入你的问题..."
                rows={1}
                className="flex-1 resize-none bg-transparent px-2 py-3 text-sm focus:outline-none max-h-32"
                style={{ overflow: "hidden" }}
                disabled={isStreaming}
              />

              {/* Send button */}
              <button
                onClick={() => handleSend()}
                disabled={isStreaming || !input.trim()}
                className="flex-shrink-0 p-2.5 mr-1 text-white rounded-xl bg-[#8a9a7e] hover:bg-[#7a8a6e] disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200 mb-0.5"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </button>
            </div>

            {/* Quick action buttons */}
            <div className="flex gap-2.5 justify-center flex-wrap mt-2.5">
              {QUICK_ACTIONS.map((action) => (
                <button
                  key={action.label}
                  onClick={() => handleSend(action.prompt)}
                  disabled={isStreaming}
                  className="px-4 py-2 text-sm rounded-full bg-white/70 backdrop-blur-sm border border-gray-200/60 text-gray-500 hover:bg-white hover:border-[#8a9a7e]/40 hover:text-[#6a7a5e] transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <span className="mr-1">{action.icon}</span>
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* Panels (modals) */}
      {nickname && (
        <>
          <UploadPanel isOpen={showUpload} onClose={() => setShowUpload(false)} nickname={nickname} />
          <DataPanel isOpen={showData} onClose={() => setShowData(false)} nickname={nickname} />
        </>
      )}
    </div>
  );
}
