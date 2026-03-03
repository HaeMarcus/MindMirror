"use client";

import { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import QuickActions from "./QuickActions";
import UploadPanel from "./UploadPanel";
import DataPanel from "./DataPanel";
import { sendMessage, getMessages, resetAll } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [showUpload, setShowUpload] = useState(false);
  const [showData, setShowData] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Load history on mount
  useEffect(() => {
    getMessages()
      .then((msgs) => {
        if (msgs.length > 0) {
          setMessages(msgs.map((m) => ({ role: m.role as "user" | "assistant", content: m.content })));
        }
      })
      .catch(() => {});
  }, []);

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || isStreaming) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setIsStreaming(true);
    setStatusText("正在处理...");

    // Add placeholder for streaming
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      await sendMessage(
        msg,
        (chunk) => {
          setStatusText("");
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last.role === "assistant") {
              return [...prev.slice(0, -1), { ...last, content: last.content + chunk }];
            }
            return prev;
          });
        },
        () => {
          setIsStreaming(false);
          setStatusText("");
        },
        (status) => {
          setStatusText(status);
        },
      );
    } catch {
      setIsStreaming(false);
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last.role === "assistant" && !last.content) {
          return [...prev.slice(0, -1), { ...last, content: "抱歉，请求出错了。请检查后端服务是否正常运行。" }];
        }
        return prev;
      });
    }
  };

  const handleReset = async () => {
    if (!confirm("确定要清除所有数据吗？（对话历史、上传的文件、记忆都会被删除）")) return;
    try {
      await resetAll();
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
    <div className="flex flex-col h-screen max-w-2xl mx-auto">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white">
        <div>
          <h1 className="text-lg font-bold text-gray-800">MindMirror</h1>
          <p className="text-xs text-gray-400">AI 自我洞察助手</p>
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
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 bg-[#f4f7f5]">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <div className="text-7xl mb-4">🪞</div>
            <p className="text-base font-medium text-gray-500">导入你的数据，然后开始对话</p>
            <p className="text-sm mt-2 text-gray-400">支持 日常记录（.html）、个人复盘（.md）、财务记账（.csv） 等多维数据</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} role={msg.role} content={msg.content} />
        ))}
        {isStreaming && messages[messages.length - 1]?.content === "" && (
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
        )}
      </div>

      {/* Quick Actions + Input */}
      <div className="border-t border-gray-200 bg-white px-4 pt-3 pb-4">
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
      <UploadPanel isOpen={showUpload} onClose={() => setShowUpload(false)} />
      <DataPanel isOpen={showData} onClose={() => setShowData(false)} />
    </div>
  );
}
