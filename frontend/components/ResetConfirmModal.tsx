"use client";

interface ResetConfirmModalProps {
  isOpen: boolean;
  isResetting: boolean;
  error: string;
  onClose: () => void;
  onConfirm: () => void;
}

export default function ResetConfirmModal({
  isOpen,
  isResetting,
  error,
  onClose,
  onConfirm,
}: ResetConfirmModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 px-4 backdrop-blur-[1px]">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="reset-dialog-title"
        className="w-full max-w-md rounded-2xl border border-white/70 bg-white p-6 shadow-2xl animate-fade-in"
      >
        <div className="flex items-start gap-3.5">
          <div className="flex h-10 w-10 flex-none items-center justify-center rounded-xl bg-[#f7f2ef] text-[#b56b58]">
            <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              <line x1="10" y1="11" x2="10" y2="17" />
              <line x1="14" y1="11" x2="14" y2="17" />
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <h2 id="reset-dialog-title" className="text-lg font-semibold text-gray-800">
              清空当前数据？
            </h2>
            <p className="mt-1.5 text-sm leading-6 text-gray-500">
              将删除当前用户的对话、上传文件和画像记忆，并退出当前账号。
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isResetting}
            aria-label="关闭清空数据确认窗口"
            className="-mr-1 -mt-1 rounded-lg p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 disabled:opacity-40"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="mt-5 rounded-xl bg-[#f7f8f6] px-4 py-3 text-xs leading-5 text-gray-500">
          此操作无法撤销。如果只想继续补充资料，可以直接使用「导入新数据」。
        </div>

        {error && (
          <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-500">{error}</p>
        )}

        <div className="mt-6 flex justify-end gap-2.5">
          <button
            type="button"
            onClick={onClose}
            disabled={isResetting}
            className="rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50 disabled:opacity-50"
          >
            保留数据
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isResetting}
            className="rounded-xl bg-[#b56b58] px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-[#a45f4e] hover:shadow disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isResetting ? "正在清空..." : "确认清空"}
          </button>
        </div>
      </div>
    </div>
  );
}
