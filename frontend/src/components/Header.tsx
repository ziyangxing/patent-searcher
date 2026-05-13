"use client";

import Link from "next/link";
import { useSearchStore } from "@/store/searchStore";

const tabs = [
  { key: "intent", label: "智能检索", href: "/search" },
  { key: "number", label: "专利号检索", href: "/patent" },
  { key: "upload", label: "上传比对", href: "/upload" },
] as const;

export function Header() {
  const { activeTab, setActiveTab } = useSearchStore();

  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
        <Link href="/" className="text-xl font-bold text-blue-600">
          PatentSearcher
        </Link>
        <nav className="flex gap-1">
          {tabs.map((tab) => (
            <Link
              key={tab.key}
              href={tab.href}
              onClick={() => setActiveTab(tab.key)}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              {tab.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
