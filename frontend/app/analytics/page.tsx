"use client";

import { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import { getAnalytics, type AnalyticsData } from "@/lib/api";

const AnalyticsDashboard = dynamic(() => import("@/components/AnalyticsDashboard"), { ssr: false });

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const d = await getAnalytics(days);
      setData(d);
    } catch {
      // silently fail
    }
    setLoading(false);
  }, [days]);

  useEffect(() => { load(); }, [load]);

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
            <button
              onClick={load}
              className="px-3 py-1.5 text-sm rounded-lg bg-[#8a9a7e] text-white hover:bg-[#7a8a6e] transition-colors"
            >
              刷新
            </button>
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
        {loading ? (
          <div className="text-center py-20 text-gray-400">加载中...</div>
        ) : data ? (
          <AnalyticsDashboard data={data} />
        ) : (
          <div className="text-center py-20 text-gray-400">暂无数据</div>
        )}
      </main>
    </div>
  );
}
