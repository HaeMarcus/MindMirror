"use client";

interface BigFive {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
}

interface RadarChartProps {
  data: BigFive | null;
}

const DIMENSIONS = [
  { key: "openness" as const, label: "开放性" },
  { key: "extraversion" as const, label: "外向性" },
  { key: "agreeableness" as const, label: "宜人性" },
  { key: "conscientiousness" as const, label: "尽责性" },
  { key: "neuroticism" as const, label: "神经质" },
];

const CENTER = 80;
const RADIUS = 60;
const LABEL_RADIUS = 75;

function polarToXY(angle: number, r: number): [number, number] {
  // Start from top (-90°), go clockwise
  const rad = ((angle - 90) * Math.PI) / 180;
  return [CENTER + r * Math.cos(rad), CENTER + r * Math.sin(rad)];
}

function getPoints(values: number[]): string {
  return values
    .map((v, i) => {
      const angle = (360 / 5) * i;
      const r = (v / 100) * RADIUS;
      const [x, y] = polarToXY(angle, r);
      return `${x},${y}`;
    })
    .join(" ");
}

function getGridPoints(level: number): string {
  return Array.from({ length: 5 })
    .map((_, i) => {
      const angle = (360 / 5) * i;
      const [x, y] = polarToXY(angle, level);
      return `${x},${y}`;
    })
    .join(" ");
}

export default function RadarChart({ data }: RadarChartProps) {
  if (!data) {
    return (
      <div className="flex flex-col items-center">
        <svg viewBox="0 0 160 160" className="w-full max-w-[180px]">
          {/* Grid lines */}
          {[0.25, 0.5, 0.75, 1].map((level) => (
            <polygon
              key={level}
              points={getGridPoints(RADIUS * level)}
              fill="none"
              stroke="#d4ddd0"
              strokeWidth="0.5"
              opacity={0.4}
            />
          ))}

          {/* Axis lines */}
          {DIMENSIONS.map((_, i) => {
            const angle = (360 / 5) * i;
            const [x, y] = polarToXY(angle, RADIUS);
            return (
              <line
                key={i}
                x1={CENTER}
                y1={CENTER}
                x2={x}
                y2={y}
                stroke="#d4ddd0"
                strokeWidth="0.5"
                opacity={0.4}
              />
            );
          })}

          {/* Labels */}
          {DIMENSIONS.map((d, i) => {
            const angle = (360 / 5) * i;
            const [x, y] = polarToXY(angle, LABEL_RADIUS);
            return (
              <text
                key={d.key}
                x={x}
                y={y}
                textAnchor="middle"
                dominantBaseline="central"
                className="fill-gray-400"
                fontSize="7"
              >
                {d.label}
              </text>
            );
          })}

          {/* Center text */}
          <text
            x={CENTER}
            y={CENTER - 4}
            textAnchor="middle"
            dominantBaseline="central"
            className="fill-gray-400"
            fontSize="7"
          >
            对话积累中
          </text>
          <text
            x={CENTER}
            y={CENTER + 6}
            textAnchor="middle"
            dominantBaseline="central"
            className="fill-gray-400"
            fontSize="7"
          >
            人格洞察即将生成...
          </text>
        </svg>
      </div>
    );
  }

  const values = DIMENSIONS.map((d) => data[d.key]);

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 160 160" className="w-full max-w-[180px]">
        {/* Grid lines */}
        {[0.25, 0.5, 0.75, 1].map((level) => (
          <polygon
            key={level}
            points={getGridPoints(RADIUS * level)}
            fill="none"
            stroke="#d4ddd0"
            strokeWidth="0.5"
            opacity={0.6}
          />
        ))}

        {/* Axis lines */}
        {DIMENSIONS.map((_, i) => {
          const angle = (360 / 5) * i;
          const [x, y] = polarToXY(angle, RADIUS);
          return (
            <line
              key={i}
              x1={CENTER}
              y1={CENTER}
              x2={x}
              y2={y}
              stroke="#d4ddd0"
              strokeWidth="0.5"
              opacity={0.6}
            />
          );
        })}

        {/* Data polygon */}
        <polygon
          points={getPoints(values)}
          fill="rgba(138, 154, 126, 0.25)"
          stroke="#8a9a7e"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />

        {/* Data points */}
        {values.map((v, i) => {
          const angle = (360 / 5) * i;
          const r = (v / 100) * RADIUS;
          const [x, y] = polarToXY(angle, r);
          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r="2.5"
              fill="#8a9a7e"
              stroke="white"
              strokeWidth="1"
            />
          );
        })}

        {/* Labels */}
        {DIMENSIONS.map((d, i) => {
          const angle = (360 / 5) * i;
          const [x, y] = polarToXY(angle, LABEL_RADIUS);
          return (
            <text
              key={d.key}
              x={x}
              y={y}
              textAnchor="middle"
              dominantBaseline="central"
              className="fill-gray-500"
              fontSize="7"
            >
              {d.label}
            </text>
          );
        })}

        {/* Score labels */}
        {values.map((v, i) => {
          const angle = (360 / 5) * i;
          const r = (v / 100) * RADIUS;
          const [x, y] = polarToXY(angle, r + 8);
          return (
            <text
              key={`score-${i}`}
              x={x}
              y={y}
              textAnchor="middle"
              dominantBaseline="central"
              className="fill-[#6a7a5e]"
              fontSize="6"
              fontWeight="600"
            >
              {v}
            </text>
          );
        })}
      </svg>
    </div>
  );
}
