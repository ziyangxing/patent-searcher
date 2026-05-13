"use client";

import { Header } from "@/components/Header";
import Link from "next/link";

export default function Home() {
  return (
    <div>
      <Header />
      <main className="mx-auto max-w-4xl px-4 py-24 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
          智能专利检索工具
        </h1>
        <p className="mt-4 text-lg text-gray-500">
          AI 驱动的专利搜索、分析与相似度比对平台
        </p>
        <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-3">
          <Link
            href="/search"
            className="rounded-2xl border border-gray-200 bg-white p-8 text-left hover:shadow-md transition-shadow"
          >
            <div className="text-2xl mb-3">&#x1F50D;</div>
            <h3 className="font-semibold text-gray-900">专利意图检索</h3>
            <p className="mt-2 text-sm text-gray-500">
              用自然语言描述技术方案，AI 自动解析意图并检索相关专利
            </p>
          </Link>
          <Link
            href="/patent"
            className="rounded-2xl border border-gray-200 bg-white p-8 text-left hover:shadow-md transition-shadow"
          >
            <div className="text-2xl mb-3">&#x1F4CB;</div>
            <h3 className="font-semibold text-gray-900">专利号精准检索</h3>
            <p className="mt-2 text-sm text-gray-500">
              输入专利号，精准定位并返回完整专利信息与法律状态
            </p>
          </Link>
          <Link
            href="/upload"
            className="rounded-2xl border border-gray-200 bg-white p-8 text-left hover:shadow-md transition-shadow"
          >
            <div className="text-2xl mb-3">&#x1F4C4;</div>
            <h3 className="font-semibold text-gray-900">上传专利找相似</h3>
            <p className="mt-2 text-sm text-gray-500">
              上传专利文档，通过 AI 语义分析检索相似专利并对比
            </p>
          </Link>
        </div>
        <div className="mt-12">
          <Link
            href="/search"
            className="inline-flex items-center rounded-xl bg-blue-600 px-8 py-3 text-base font-medium text-white hover:bg-blue-700 transition-colors"
          >
            开始检索
          </Link>
        </div>
      </main>
    </div>
  );
}
