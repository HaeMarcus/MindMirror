"use client";

import { useState, useRef } from "react";
import { uploadFile, UploadProgress } from "@/lib/api";

interface UploadResult {
  source_name: string;
  source_type: string;
  chunk_count: number;
  time_range_start: string | null;
  time_range_end: string | null;
}

interface UploadPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function UploadPanel({ isOpen, onClose }: UploadPanelProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<UploadProgress | null>(null);
  const [results, setResults] = useState<UploadResult[]>([]);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setError("");
    setUploading(true);
    setProgress(null);

    const newResults: UploadResult[] = [];
    for (const file of Array.from(files)) {
      try {
        const res = await uploadFile(file, (p) => setProgress(p));
        newResults.push(res);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "上传失败";
        setError(msg);
      }
    }

    setResults((prev) => [...newResults, ...prev]);
    setUploading(false);
    setProgress(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  };

  const SOURCE_LABELS: Record<string, string> = {
    flomo_html: "Flomo 日常记录",
    review_md: "Markdown 文档",
    ledger_csv: "钱迹账单",
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
      <div className="bg-white rounded-2xl w-full max-w-lg mx-4 p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800">导入数据</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>

        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => !uploading && fileRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${uploading ? "border-[#8a9a7e] bg-[#f4f7f5]" : "border-gray-300 cursor-pointer hover:border-gray-400 hover:bg-gray-50"}`}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".html,.htm,.md,.csv"
            multiple
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />
          {uploading && progress ? (
            <div>
              <p className="text-[#7a8a72] text-sm font-medium mb-2">{progress.message}</p>
              <p className="text-[#8a9a7e] text-xs mb-2">
                当前进度：{progress.current} / {progress.total}
              </p>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className="bg-[#8a9a7e] h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${Math.round((progress.current / progress.total) * 100)}%` }}
                />
              </div>
            </div>
          ) : uploading ? (
            <p className="text-gray-500 text-sm">解析文件中...</p>
          ) : (
            <>
              <p className="text-gray-500 text-sm mb-1">拖拽文件到此处，或点击选择</p>
              <p className="text-gray-400 text-xs">支持 .html（Flomo）、.md（复盘）、.csv（钱迹）</p>
            </>
          )}
        </div>

        {error && <p className="text-red-500 text-xs mt-2">{error}</p>}

        {results.length > 0 && (
          <div className="mt-4 space-y-2 max-h-48 overflow-y-auto">
            {results.map((r, i) => (
              <div key={i} className="bg-gray-50 rounded-lg px-3 py-2 text-xs">
                <div className="font-medium text-gray-700">
                  {SOURCE_LABELS[r.source_type] || r.source_type} — {r.source_name}
                </div>
                <div className="text-gray-500 mt-0.5">
                  {r.chunk_count} 个片段
                  {r.time_range_start && ` · ${r.time_range_start}`}
                  {r.time_range_end && r.time_range_end !== r.time_range_start && ` ~ ${r.time_range_end}`}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
