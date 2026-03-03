"use client";

import { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import QuickActions from "./QuickActions";
import UploadPanel from "./UploadPanel";
import DataPanel from "./DataPanel";
import NicknamePrompt from "./NicknamePrompt";
import { sendMessage, getMessages, resetAll, submitFeedback } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  messageId?: number | null;
  feedbackGiven?: "accurate" | "inaccurate" | null;
}

export default function ChatWindow() {
  const [nickname, setNickname] = useState<string | null>(null);
  const [showNicknamePrompt, setShowNicknamePrompt] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [showUpload, setShowUpload] = useState(false);
  const [showData, setShowData] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const streamBuffer = useRef("");
  const [streamingContent, setStreamingContent] = useState("");

  // Initialize nickname from localStorage
  useEffect(() => {
    const stored = localStorage.getItem("mm_nickname");
    if (stored) {
      setNickname(stored);
    } else {
      setShowNicknamePrompt(true);
    }
  }, []);

  // Load history when nickname is set
  useEffect(() => {
    if (!nickname) return;
    getMessages(nickname)
      .then((msgs) => {
        if (msgs.length > 0) {
          setMessages(msgs.map((m) => ({ role: m.role as "user" | "assistant", content: m.content })));
        }
      })
      .catch(() => {});
  }, [nickname]);

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isStreaming, streamingContent]);

  const handleNicknameConfirm = (name: string) => {
    setNickname(name);
    setShowNicknamePrompt(false);
  };

  const handleSend = async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || isStreaming || !nickname) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
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
        (messageId) => {
          const fullContent = streamBuffer.current;
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: fullContent, messageId, feedbackGiven: null },
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
      await submitFeedback(msg.messageId, rating);
    } catch {
      // silently fail
    }
  };

  const handleReset = async () => {
    if (!nickname) return;
    if (!confirm("确定要清除所有数据吗？（对话历史、上传的文件、记忆都会被删除）")) return;
    try {
      await resetAll(nickname);
      setMessages([]);
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

  return (
    <div className="flex flex-col h-screen w-full max-w-2xl lg:max-w-4xl xl:max-w-5xl mx-auto">
      {/* Nickname Prompt */}
      {showNicknamePrompt && <NicknamePrompt onConfirm={handleNicknameConfirm} />}

      {/* Header */}
      <header className="flex items-center justify-between px-4 lg:px-8 py-3 border-b border-gray-200 bg-white">
        <div>
          <h1 className="text-lg font-bold text-gray-800">MindMirror</h1>
          <p className="text-xs text-gray-400">基于多源数据的 AI 觉察助手{nickname && ` · ${nickname}`}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleReset}
            className="px-3 py-1.5 text-xs rounded-lg border border-[#a8b5a0] text-[#7a8a72] hover:bg-[#f0f4ee] transition-colors"
          >
            清除数据
          </button>
          <button
            onClick={() => setShowData(true)}
            className="px-3 py-1.5 text-xs rounded-lg border border-[#a8b5a0] text-[#7a8a72] hover:bg-[#f0f4ee] transition-colors"
          >
            当前数据库
          </button>
          <button
            onClick={() => setShowUpload(true)}
            className="px-3 py-1.5 text-xs rounded-lg bg-[#8a9a7e] text-white hover:bg-[#7a8a6e] transition-colors"
          >
            导入数据
          </button>
        </div>
      </header>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 lg:px-8 py-4 bg-[#f4f7f5]">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <div className="text-7xl mb-4">🪞</div>
            <p className="text-base font-medium text-gray-500">导入你的数据，然后开始对话</p>
            <p className="text-sm mt-2 text-gray-400">支持 日常记录（.html）、个人复盘（.md）、财务记账（.csv） 等多维数据</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            role={msg.role}
            content={msg.content}
            feedbackGiven={msg.feedbackGiven}
            onFeedback={msg.role === "assistant" && msg.messageId ? (rating) => handleFeedback(i, rating) : undefined}
          />
        ))}
        {isStreaming && (
          streamingContent ? (
            <MessageBubble role="assistant" content={streamingContent} isStreaming />
          ) : (
            <div className="flex justify-start mb-4">
              <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                  {statusText && (
                    <span className="text-xs text-gray-400">{statusText}</span>
                  )}
                </div>
              </div>
            </div>
          )
        )}
      </div>

      {/* Quick Actions + Input */}
      <div className="border-t border-gray-200 bg-white px-4 lg:px-8 pt-3 pb-4">
        <div className="mb-3">
          <QuickActions onSelect={handleSend} disabled={isStreaming} />
        </div>

        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的问题..."
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-2.5 text-sm focus:outline-none focus:border-gray-500 transition-colors"
            disabled={isStreaming}
          />
          <button
            onClick={() => handleSend()}
            disabled={isStreaming || !input.trim()}
            className="px-4 py-2.5 rounded-xl bg-[#8a9a7e] text-white text-sm font-medium hover:bg-[#7a8a6e] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            发送
          </button>
        </div>

        <p className="text-center text-xs text-gray-400 mt-2">🔒 隐私持续守护中 · 原始数据不上传</p>
      </div>

      {/* Panels */}
      {nickname && (
        <>
          <UploadPanel isOpen={showUpload} onClose={() => setShowUpload(false)} nickname={nickname} />
          <DataPanel isOpen={showData} onClose={() => setShowData(false)} nickname={nickname} />
        </>
      )}
    </div>
  );
}
