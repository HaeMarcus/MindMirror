"use client";

import { useState } from "react";
import { registerNickname, startDemo } from "@/lib/api";

interface NicknamePromptProps {
  onConfirm: (nickname: string, displayName: string, isDemo: boolean) => void;
}

export default function NicknamePrompt({ onConfirm }: NicknamePromptProps) {
  const [value, setValue] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState<"nickname" | "demo" | null>(null);

  const handleSubmit = async () => {
    if (loading) return;
    const nickname = value.trim();
    if (!nickname) {
      setError("请输入你的昵称");
      return;
    }

    setLoading("nickname");
    setError("");

    try {
      const res = await registerNickname(nickname);
      if (res.error) {
        setError(res.error);
        setLoading(null);
        return;
      }
      localStorage.setItem("mm_nickname", nickname);
      localStorage.setItem("mm_display_name", nickname);
      localStorage.removeItem("mm_is_demo");
      onConfirm(nickname, nickname, false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "网络错误，请稍后重试");
      setLoading(null);
    }
  };

  const handleDemo = async () => {
    if (loading) return;
    setLoading("demo");
    setError("");
    try {
      const session = await startDemo();
      localStorage.setItem("mm_nickname", session.nickname);
      localStorage.setItem("mm_display_name", session.display_name);
      localStorage.setItem("mm_is_demo", "true");
      onConfirm(session.nickname, session.display_name, true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "示例人物准备失败，请稍后重试");
      setLoading(null);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-white/90 backdrop-blur-md rounded-2xl w-full max-w-sm mx-4 p-8 shadow-2xl text-center animate-fade-in">
        <div className="text-5xl mb-4 animate-float">🪞</div>
        <h2 className="text-lg font-semibold text-gray-800 mb-1">你好，我是 MindMirror</h2>
        <p className="text-sm text-gray-400 mb-6">该怎么称呼你？</p>

        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入你的昵称"
          autoFocus
          className="w-full rounded-xl border border-gray-200 bg-white/80 px-4 py-2.5 text-sm text-center focus:outline-none focus:border-[#8a9a7e] focus:shadow-sm transition-all duration-200"
          disabled={!!loading}
        />

        {error && <p className="text-red-500 text-xs mt-2">{error}</p>}

        <button
          onClick={handleSubmit}
          disabled={!!loading || !value.trim()}
          className="w-full mt-4 px-4 py-2.5 rounded-xl bg-[#8a9a7e] text-white text-sm font-medium hover:bg-[#7a8a6e] disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
        >
          {loading === "nickname" ? "确认中..." : "开始探索"}
        </button>

        <div className="flex items-center gap-3 my-4 text-xs text-gray-300">
          <span className="h-px flex-1 bg-gray-200" />
          <span>或</span>
          <span className="h-px flex-1 bg-gray-200" />
        </div>

        <button
          onClick={handleDemo}
          disabled={!!loading}
          className="w-full px-4 py-2.5 rounded-xl border border-[#8a9a7e]/40 bg-[#f6f9f4] text-[#6a7a5e] text-sm font-medium hover:bg-[#edf3e9] disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
        >
          {loading === "demo" ? "正在准备虚构示例数据..." : "直接体验虚构示例人物"}
        </button>
        <p className="mt-2 text-[11px] leading-relaxed text-gray-400">
          示例人物“许遥”及其日记、复盘和账单均为虚构内容
        </p>
      </div>
    </div>
  );
}
