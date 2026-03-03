import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MindMirror",
  description: "AI 自我洞察助手",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
