"use client";

interface QuickActionsProps {
  onSelect: (prompt: string) => void;
  disabled: boolean;
}

const ACTIONS = [
  {
    label: "大五人格与MBTI",
    icon: "👤",
    prompt: "请基于我所有的数据，从大五人格（开放性、尽责性、外向性、宜人性、神经质）的角度分析我的人格特征。并推断我的 MBTI 类型。",
  },
  {
    label: "言行一致性洞察",
    icon: "🔍",
    prompt: "请基于我所有的数据，归纳我言语与行为的不一致之处。比如我经常说想要学习，但是账单数据却显示我最近三个月在'学习'类支出占比下降了 40%。",
  },
  {
    label: "消费观念洞察",
    icon: "💰",
    prompt: "请基于我所有的数据，尤其是账单数据，结合我的语言表达，分析我的消费习惯和消费观念。",
  },
];

export default function QuickActions({ onSelect, disabled }: QuickActionsProps) {
  return (
    <div className="flex gap-2 justify-start flex-wrap">
      {ACTIONS.map((action) => (
        <button
          key={action.label}
          onClick={() => onSelect(action.prompt)}
          disabled={disabled}
          className="px-3 py-1.5 text-xs rounded-full bg-[#e8f0fb] text-[#4a6fa5] hover:bg-[#d6e4f5] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <span className="mr-1">{action.icon}</span>
          {action.label}
        </button>
      ))}
    </div>
  );
}
