"use client";

import { useState } from "react";
import { registerNickname } from "@/lib/api";

interface NicknamePromptProps {
  onConfirm: (nickname: string) => void;
}

export default function NicknamePrompt({ onConfirm }: NicknamePromptProps) {
  const [value, setValue] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    const nickname = value.trim();
    if (!nickname) {
      setError("请输入你的昵称");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await registerNickname(nickname);
      if (res.error) {
        setError(res.error);
        setLoading(false);
        return;
      }
      localStorage.setItem("mm_nickname", nickname);
      onConfirm(nickname);
    } catch {
      setError("网络错误，请稍后重试");
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
      <div className="bg-white rounded-2xl w-full max-w-sm mx-4 p-6 shadow-2xl text-center">
        <div className="text-5xl mb-4">🪞</div>
        <h2 className="text-lg font-semibold text-gray-800 mb-1">你好，我是 MindMirror</h2>
        <p className="text-sm text-gray-400 mb-5">该怎么称呼你？</p>

        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入你的昵称"
          autoFocus
          className="w-full rounded-xl border border-gray-300 px-4 py-2.5 text-sm text-center focus:outline-none focus:border-[#8a9a7e] transition-colors"
          disabled={loading}
        />

        {error && <p className="text-red-500 text-xs mt-2">{error}</p>}

        <button
          onClick={handleSubmit}
          disabled={loading || !value.trim()}
          className="w-full mt-4 px-4 py-2.5 rounded-xl bg-[#8a9a7e] text-white text-sm font-medium hover:bg-[#7a8a6e] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "确认中..." : "开始探索"}
        </button>
      </div>
    </div>
  );
}
