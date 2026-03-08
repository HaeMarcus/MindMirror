"use client";

import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import type { AnalyticsData } from "@/lib/api";

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="text-sm text-gray-500 mb-1">{label}</div>
      <div className="text-3xl font-bold text-gray-800">{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}

export default function AnalyticsDashboard({ data }: { data: AnalyticsData }) {
  const trendWithRate = data.trend.map((d) => {
    const total = d.accurate + d.inaccurate;
    return { ...d, rate: total > 0 ? Math.round(d.accurate / total * 100) : null, total };
  });

  const versionWithRate = data.by_version.map((v) => {
    const total = v.accurate + v.inaccurate;
    return { ...v, rate: total > 0 ? Math.round(v.accurate / total * 100) : 0, total };
  });

  const userWithRate = data.by_user
    .map((u) => {
      const total = u.accurate + u.inaccurate;
      return { ...u, rate: total > 0 ? Math.round(u.accurate / total * 100) : 0, total };
    })
    .sort((a, b) => b.total - a.total);

  return (
    <div className="space-y-6">
      {/* Top-level KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="有效洞察确认率"
          value={`${data.rate}%`}
          sub="北极星指标"
        />
        <StatCard label="总反馈数" value={String(data.total)} />
        <StatCard label="准确" value={String(data.accurate)} sub={`${data.total > 0 ? Math.round(data.accurate / data.total * 100) : 0}%`} />
        <StatCard label="不准确" value={String(data.inaccurate)} sub={`${data.total > 0 ? Math.round(data.inaccurate / data.total * 100) : 0}%`} />
      </div>

      {/* Daily trend chart */}
      {trendWithRate.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">每日确认率趋势</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendWithRate}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} unit="%" />
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              <Tooltip formatter={((v: any, n: any) => n === "rate" ? [`${v}%`, "确认率"] : [String(v), n === "accurate" ? "准确" : "不准确"]) as any} />
              <Line type="monotone" dataKey="rate" stroke="#8a9a7e" strokeWidth={2} dot={{ r: 4 }} name="rate" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Daily feedback volume */}
      {trendWithRate.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">每日反馈量</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={trendWithRate}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              <Tooltip formatter={((v: any, n: any) => [String(v), n === "accurate" ? "准确" : "不准确"]) as any} />
              <Legend formatter={(v) => (v === "accurate" ? "准确" : "不准确")} />
              <Bar dataKey="accurate" stackId="a" fill="#86a17a" />
              <Bar dataKey="inaccurate" stackId="a" fill="#d98a8a" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Version comparison */}
      {versionWithRate.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">版本对比</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={versionWithRate}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="version" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} unit="%" />
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              <Tooltip formatter={((v: any, n: any) => n === "rate" ? [`${v}%`, "确认率"] : [String(v), n]) as any} />
              <Bar dataKey="rate" fill="#8a9a7e" name="rate" />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2 pr-4">版本</th>
                  <th className="pb-2 pr-4">准确</th>
                  <th className="pb-2 pr-4">不准确</th>
                  <th className="pb-2 pr-4">总计</th>
                  <th className="pb-2">确认率</th>
                </tr>
              </thead>
              <tbody>
                {versionWithRate.map((v) => (
                  <tr key={v.version} className="border-b border-gray-100">
                    <td className="py-2 pr-4 font-mono">{v.version}</td>
                    <td className="py-2 pr-4 text-green-600">{v.accurate}</td>
                    <td className="py-2 pr-4 text-red-500">{v.inaccurate}</td>
                    <td className="py-2 pr-4">{v.total}</td>
                    <td className="py-2 font-semibold">{v.rate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Per-user stats */}
      {userWithRate.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">用户维度</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-2 pr-4">用户</th>
                <th className="pb-2 pr-4">准确</th>
                <th className="pb-2 pr-4">不准确</th>
                <th className="pb-2 pr-4">总计</th>
                <th className="pb-2">确认率</th>
              </tr>
            </thead>
            <tbody>
              {userWithRate.map((u) => (
                <tr key={u.user} className="border-b border-gray-100">
                  <td className="py-2 pr-4">{u.user || "(未知)"}</td>
                  <td className="py-2 pr-4 text-green-600">{u.accurate}</td>
                  <td className="py-2 pr-4 text-red-500">{u.inaccurate}</td>
                  <td className="py-2 pr-4">{u.total}</td>
                  <td className="py-2 font-semibold">{u.rate}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Recent feedback log */}
      {data.recent.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">最近反馈记录</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2 pr-3">时间</th>
                  <th className="pb-2 pr-3">用户</th>
                  <th className="pb-2 pr-3">评价</th>
                  <th className="pb-2 pr-3">版本</th>
                  <th className="pb-2">数据来源</th>
                </tr>
              </thead>
              <tbody>
                {data.recent.map((r) => (
                  <tr key={r.id} className="border-b border-gray-100">
                    <td className="py-1.5 pr-3 text-gray-500 whitespace-nowrap">{r.created_at}</td>
                    <td className="py-1.5 pr-3">{r.user_id || "-"}</td>
                    <td className="py-1.5 pr-3">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-xs ${
                        r.rating === "accurate" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                      }`}>
                        {r.rating === "accurate" ? "准确" : "不准确"}
                      </span>
                    </td>
                    <td className="py-1.5 pr-3 font-mono text-gray-500">{r.app_version || "-"}</td>
                    <td className="py-1.5 text-gray-500">{r.source_types || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state */}
      {data.total === 0 && (
        <div className="text-center py-16 text-gray-400">
          <div className="text-5xl mb-4">📊</div>
          <p className="text-base">暂无反馈数据</p>
          <p className="text-sm mt-1">用户在对话中点击「很准确」或「不准确」后，数据会出现在这里</p>
        </div>
      )}
    </div>
  );
}
