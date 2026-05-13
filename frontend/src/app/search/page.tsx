"use client";

import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useSearchStore, PatentResult } from "@/store/searchStore";
import { useState, useRef, useCallback } from "react";
import { apiPost } from "@/lib/api";

interface SearchPlan {
  technical_field: string;
  core_features: string[];
  keywords: string[];
  ipc_codes: string[];
  expanded_queries: string[];
}

export default function SearchPage() {
  const { query, setQuery, results, setResults, isLoading, setLoading } =
    useSearchStore();
  const [aiAnalysis, setAiAnalysis] = useState("");
  const [plan, setPlan] = useState<SearchPlan | null>(null);
  const [statusMessage, setStatusMessage] = useState("");
  const [foundCount, setFoundCount] = useState(0);
  const [topK, setTopK] = useState(20);
  const abortRef = useRef<AbortController | null>(null);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResults([]);
    setAiAnalysis("");
    setPlan(null);
    setStatusMessage("正在检索...");
    setFoundCount(0);

    try {
      const data = await apiPost<{
        plan?: SearchPlan;
        results: PatentResult[];
        analysis?: string;
        total: number;
        message?: string;
      }>("/search/intent", { query, top_k: topK });

      if (data.plan) {
        setPlan(data.plan);
      }
      if (data.results) setResults(data.results);
      if (data.analysis) setAiAnalysis(data.analysis);
      if (data.message) setStatusMessage(data.message);
      setFoundCount(data.total || 0);
      if (!data.message) setStatusMessage(`检索完成，共 ${data.total || 0} 条结果`);
    } catch (err) {
      const msg = `搜索失败: ${(err as Error).message}`;
      setStatusMessage(msg);
      setAiAnalysis(msg);
    } finally {
      setLoading(false);
    }
  }, [query, topK, setLoading, setResults]);

  return (
    <div>
      <Header />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <h2 className="text-2xl font-bold text-gray-900">专利意图检索</h2>
        <p className="mt-1 text-sm text-gray-500">
          用自然语言描述您要检索的技术方案，AI 将自动分析并返回相关专利
        </p>

        <div className="mt-6 flex gap-3 items-end">
          <div className="flex-1">
            <Input
              placeholder="例如：共轴双旋翼无人机 飞行控制..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
          </div>
          <div className="w-24">
            <label className="block text-xs text-gray-400 mb-1">结果数</label>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-full h-10 rounded-lg border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>
          <Button size="lg" onClick={handleSearch} disabled={isLoading}>
            {isLoading ? "检索中..." : "检索"}
          </Button>
        </div>

        {isLoading && statusMessage && (
          <div className="mt-4 flex items-center gap-3 text-sm text-blue-600">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
            {statusMessage}
          </div>
        )}

        {plan && (
          <Card className="mt-4">
            <CardContent className="pt-4">
              <div className="flex flex-wrap gap-4 text-sm">
                {plan.technical_field && (
                  <div>
                    <span className="text-gray-400">技术领域：</span>
                    <span className="text-gray-700">{plan.technical_field}</span>
                  </div>
                )}
                {plan.ipc_codes.length > 0 && (
                  <div>
                    <span className="text-gray-400">IPC：</span>
                    {plan.ipc_codes.map((c) => (
                      <span key={c} className="ml-1 rounded bg-gray-100 px-1.5 py-0.5 text-xs">
                        {c}
                      </span>
                    ))}
                  </div>
                )}
                {plan.keywords.length > 0 && (
                  <div>
                    <span className="text-gray-400">关键词：</span>
                    <span className="text-gray-700">
                      {plan.keywords.slice(0, 8).join(", ")}
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {results.length > 0 && (
          <div className="mt-8 grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-4">
              <h3 className="font-semibold text-gray-700">
                检索结果 ({results.length} / {foundCount || results.length} 条)
              </h3>
              {results.map((r, i) => (
                <Card key={i}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-xs text-blue-600 font-mono">
                          {r.patent_number}
                        </span>
                        <h4 className="font-semibold text-gray-900 mt-1">
                          {r.title}
                        </h4>
                      </div>
                      {r.similarity_score != null && (
                        <span className="rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
                          {r.similarity_score}%
                        </span>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 line-clamp-3">
                      {r.abstract}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {r.ipc_codes?.map((code) => (
                        <span
                          key={code}
                          className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                        >
                          {code}
                        </span>
                      ))}
                      {r.applicants?.map((app) => (
                        <span
                          key={app}
                          className="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-600"
                        >
                          {app}
                        </span>
                      ))}
                    </div>
                    <div className="mt-3 flex gap-2 border-t pt-2">
                      {r.google_url && (
                        <a
                          href={r.google_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-600 hover:underline"
                        >
                          Google Patents ↗
                        </a>
                      )}
                      {r.espacenet_url && (
                        <a
                          href={r.espacenet_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-600 hover:underline"
                        >
                          Espacenet ↗
                        </a>
                      )}
                      <a
                        href={`/patent/${encodeURIComponent(r.patent_number)}`}
                        className="text-xs text-blue-600 hover:underline"
                      >
                        AI 问答 ↗
                      </a>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div>
              <Card>
                <CardHeader>
                  <h3 className="font-semibold text-gray-700">AI 分析</h3>
                </CardHeader>
                <CardContent>
                  {aiAnalysis ? (
                    <p className="text-sm text-gray-600 whitespace-pre-wrap">
                      {aiAnalysis}
                    </p>
                  ) : (
                    <p className="text-sm text-gray-400">
                      {isLoading ? "分析生成中..." : "等待检索结果..."}
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
