"use client";

interface QuickActionsProps {
  onSelect: (prompt: string) => void;
  disabled: boolean;
}

const ACTIONS = [
  {
    label: "大五人格分析",
    prompt: "请基于我所有的数据，从大五人格（开放性、尽责性、外向性、宜人性、神经质）的角度分析我的人格特征。",
  },
  {
    label: "MBTI 行为分析",
    prompt: "请基于我所有的数据，从 MBTI 的角度分析我的行为模式和认知偏好。不需要给我贴标签，而是分析具体的行为证据。",
  },
  {
    label: "职业优劣势",
    prompt: "请基于我所有的数据，分析我的职业优势和劣势。从行为模式、价值取向、能力倾向等方面展开。",
  },
];

export default function QuickActions({ onSelect, disabled }: QuickActionsProps) {
  return (
    <div className="flex gap-2 justify-center flex-wrap">
      {ACTIONS.map((action) => (
        <button
          key={action.label}
          onClick={() => onSelect(action.prompt)}
          disabled={disabled}
          className="px-3 py-1.5 text-xs rounded-full border border-gray-300 text-gray-600 hover:bg-gray-100 hover:border-gray-400 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}
