"use client";

import { useState, useEffect } from "react";
import RadarChart from "./RadarChart";
import { getProfile, type BigFive } from "@/lib/api";

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  nickname: string;
  onOpenUpload: () => void;
  onOpenData: () => void;
  onReset: () => void;
}

function getDaysAgo(dateStr: string | null): number | null {
  if (!dateStr) return null;
  const created = new Date(dateStr + "Z");
  const now = new Date();
  const diff = Math.floor((now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24));
  return Math.max(diff, 0);
}

export default function Sidebar({
  isOpen,
  onToggle,
  nickname,
  onOpenUpload,
  onOpenData,
  onReset,
}: SidebarProps) {
  const [bigFive, setBigFive] = useState<BigFive | null>(null);
  const [companionDays, setCompanionDays] = useState<number | null>(null);

  // Load profile when sidebar opens
  useEffect(() => {
    if (!isOpen || !nickname) return;
    getProfile(nickname)
      .then((data) => {
        if (data.profile.big_five) setBigFive(data.profile.big_five);
        const days = getDaysAgo(data.created_at);
        setCompanionDays(days);
      })
      .catch(() => {});
  }, [isOpen, nickname]);

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-30 md:hidden transition-opacity"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed md:relative z-40 h-full
          bg-gradient-to-b from-[#f0f4ee] to-[#e4ebe0]
          border-r border-[#d4ddd0]
          flex flex-col
          transition-all duration-300 ease-in-out
          ${isOpen ? "w-60" : "w-0 md:w-0"}
          overflow-hidden
        `}
      >
        <div className="flex flex-col h-full w-60 min-w-[15rem]">
          {/* Sidebar header — logo + collapse button */}
          <div className="flex items-center justify-between px-4 pt-5 pb-1">
            <div className="flex items-center gap-2">
              <span className="text-xl">🪞</span>
              <span className="font-bold text-gray-800 text-lg">MindMirror</span>
            </div>
            <button
              onClick={onToggle}
              className="p-1 rounded-md hover:bg-[#d4ddd0]/50 text-gray-500 transition-colors"
              title="收起侧栏"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <line x1="9" y1="3" x2="9" y2="21" />
                <polyline points="15 8 12 12 15 16" />
              </svg>
            </button>
          </div>

          {/* User greeting capsule */}
          <div className="px-3 pt-3 pb-4">
            <div className="flex flex-col items-center gap-1 px-2.5 py-2.5 rounded-xl bg-[#e8ede4]/70 backdrop-blur-sm border border-[#d4ddd0]/40 transition-all duration-200 cursor-default">
              <span className="text-sm text-gray-700 font-medium truncate w-full text-center">
                你好，{nickname} 👋
              </span>
              {companionDays !== null && (
                <span className="text-[11px] text-gray-400">
                  已陪伴你 {companionDays} 天
                </span>
              )}
            </div>
          </div>

          {/* Data management section */}
          <div className="px-3 pb-2">
            <div className="flex items-center gap-2 px-1 mb-2.5 pt-1">
              <div className="w-[3px] h-4 rounded-full bg-[#8a9a7e]" />
              <span className="text-sm font-bold text-gray-700">数据管理</span>
            </div>
            <div className="space-y-0.5">
              <button
                onClick={onOpenUpload}
                className="w-full flex items-center gap-2.5 px-2.5 py-2 text-sm text-gray-600 rounded-lg hover:bg-[#d4ddd0]/50 hover:translate-x-0.5 transition-all"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                导入新数据
              </button>
              <button
                onClick={onOpenData}
                className="w-full flex items-center gap-2.5 px-2.5 py-2 text-sm text-gray-600 rounded-lg hover:bg-[#d4ddd0]/50 hover:translate-x-0.5 transition-all"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <ellipse cx="12" cy="5" rx="9" ry="3" />
                  <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
                  <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
                </svg>
                当前数据库
              </button>
              <button
                onClick={onReset}
                className="w-full flex items-center gap-2.5 px-2.5 py-2 text-sm text-gray-500 rounded-lg hover:bg-red-50 hover:text-red-500 hover:translate-x-0.5 transition-all"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                </svg>
                清空数据
              </button>
            </div>
          </div>

          {/* Big Five Radar Chart */}
          <div className="px-3 pt-3 flex-1">
            <div className="flex items-center gap-2 px-1 mb-2 pt-1">
              <div className="w-[3px] h-4 rounded-full bg-[#f97316]" />
              <span className="text-sm font-bold text-gray-700">大五人格画像</span>
            </div>
            <RadarChart data={bigFive} />
          </div>

          {/* Feedback guidance */}
          <div className="px-4 py-3">
            <div className="rounded-xl bg-white/50 backdrop-blur-sm px-3 py-2.5">
              <p className="text-[11px] text-gray-500 leading-relaxed">
                每次对话后，欢迎点击 👍👎 反馈洞察是否准确，帮助我们持续改进
              </p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
