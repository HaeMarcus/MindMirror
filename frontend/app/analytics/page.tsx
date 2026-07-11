"use client";

import { FormEvent, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { getAnalytics, type AnalyticsData } from "@/lib/api";

const AnalyticsDashboard = dynamic(() => import("@/components/AnalyticsDashboard"), { ssr: false });

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState("");
  const [tokenInput, setTokenInput] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const savedToken = sessionStorage.getItem("mm_admin_token") || "";
    if (savedToken) {
      setTokenInput(savedToken);
      setToken(savedToken);
    }
  }, []);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;
    setLoading(true);
    setError("");

    getAnalytics(days, token)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err: Error) => {
        if (cancelled) return;
        setData(null);
        setError(err.message);
        sessionStorage.removeItem("mm_admin_token");
        setToken("");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [days, token]);

  const unlock = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextToken = tokenInput.trim();
    if (!nextToken) return;
    sessionStorage.setItem("mm_admin_token", nextToken);
    setToken(nextToken);
  };

  const lock = () => {
    sessionStorage.removeItem("mm_admin_token");
    setToken("");
    setTokenInput("");
    setData(null);
    setError("");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-800">MindMirror Analytics</h1>
            <p className="text-sm text-gray-400">北极星指标：有效洞察确认率</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none"
            >
              <option value={7}>近 7 天</option>
              <option value={30}>近 30 天</option>
              <option value={90}>近 90 天</option>
              <option value={365}>全部</option>
            </select>
            {token && (
              <button
                onClick={lock}
                className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
              >
                锁定看板
              </button>
            )}
            <a
              href="/"
              className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
            >
              返回主页
            </a>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6">
        {!token ? (
          <div className="max-w-md mx-auto mt-20 rounded-2xl border border-gray-200 bg-white p-7 shadow-sm">
            <div className="text-3xl mb-3">🔐</div>
            <h2 className="text-lg font-semibold text-gray-800">开发者看板</h2>
            <p className="mt-1 text-sm leading-relaxed text-gray-500">
              输入服务器中配置的管理令牌后查看反馈数据。令牌仅保存在当前浏览器标签页。
            </p>
            <form onSubmit={unlock} className="mt-5 space-y-3">
              <input
                type="password"
                autoComplete="current-password"
                value={tokenInput}
                onChange={(event) => setTokenInput(event.target.value)}
                placeholder="输入 ADMIN_TOKEN"
                className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-sm focus:border-[#8a9a7e] focus:outline-none"
              />
              {error && <p className="text-sm text-red-500">{error}</p>}
              <button
                type="submit"
                disabled={!tokenInput.trim()}
                className="w-full rounded-xl bg-[#8a9a7e] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#7a8a6e] disabled:cursor-not-allowed disabled:opacity-40"
              >
                解锁看板
              </button>
            </form>
          </div>
        ) : loading ? (
          <div className="text-center py-20 text-gray-400">加载中...</div>
        ) : data ? (
          <AnalyticsDashboard data={data} />
        ) : (
          <div className="text-center py-20 text-gray-400">看板加载失败</div>
        )}
      </main>
    </div>
  );
}
