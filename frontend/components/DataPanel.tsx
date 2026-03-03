"use client";

import { useState, useEffect } from "react";
import { getDocuments, DocumentInfo } from "@/lib/api";

interface DataPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const SOURCE_LABELS: Record<string, string> = {
  flomo_html: "Flomo 日常记录",
  review_md: "Markdown 文档",
  ledger_csv: "钱迹账单",
};

const SOURCE_ICONS: Record<string, string> = {
  flomo_html: "📝",
  review_md: "📄",
  ledger_csv: "💰",
};

export default function DataPanel({ isOpen, onClose }: DataPanelProps) {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      getDocuments()
        .then(setDocuments)
        .catch(() => setDocuments([]))
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const totalChunks = documents.reduce((sum, d) => sum + d.chunk_count, 0);

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
      <div className="bg-white rounded-2xl w-full max-w-lg mx-4 p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">当前数据库</h2>
            {!loading && documents.length > 0 && (
              <p className="text-xs text-gray-400 mt-0.5">
                {documents.length} 个数据源 · {totalChunks} 个知识片段
              </p>
            )}
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>

        {loading ? (
          <div className="py-12 text-center text-sm text-gray-400">加载中...</div>
        ) : documents.length === 0 ? (
          <div className="py-12 text-center">
            <div className="text-3xl mb-2">📭</div>
            <p className="text-sm text-gray-400">还没有导入任何数据</p>
            <p className="text-xs text-gray-300 mt-1">点击「导入数据」上传你的文件</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {documents.map((doc) => (
              <div key={doc.doc_id} className="bg-gray-50 rounded-xl px-4 py-3">
                <div className="flex items-start gap-2">
                  <span className="text-lg mt-0.5">{SOURCE_ICONS[doc.source_type] || "📁"}</span>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm text-gray-700 truncate">
                      {doc.source_name}
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5">
                      {SOURCE_LABELS[doc.source_type] || doc.source_type} · {doc.chunk_count} 个片段
                    </div>
                    {doc.time_range_start && (
                      <div className="text-xs text-gray-400 mt-0.5">
                        {doc.time_range_start}
                        {doc.time_range_end && doc.time_range_end !== doc.time_range_start && ` ~ ${doc.time_range_end}`}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
