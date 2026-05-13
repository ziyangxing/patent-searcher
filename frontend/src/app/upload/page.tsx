"use client";

import { Header } from "@/components/Header";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useCallback, useState, useRef } from "react";
import { useDropzone } from "react-dropzone";

interface PatentFeatures {
  title: string;
  technical_field: string;
  core_innovations: string[];
  ipc_codes: string[];
  keywords: string[];
  problem_statement: string;
  technical_solution: string;
}

interface SimilarResult {
  patent_number: string;
  title: string;
  abstract: string;
  similarity_score: number;
  comparison?: string;
  tech_overlap?: string;
  claim_overlap?: string;
  differences?: string;
  ipc_codes?: string[];
  applicants?: string[];
}

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [fileText, setFileText] = useState("");
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState("");
  const [features, setFeatures] = useState<PatentFeatures | null>(null);
  const [results, setResults] = useState<SimilarResult[]>([]);
  const [comparisons, setComparisons] = useState<Record<string, SimilarResult>>({});
  const [summary, setSummary] = useState("");
  const [foundCount, setFoundCount] = useState(0);
  const abortRef = useRef<AbortController | null>(null);

  const onDrop = useCallback(async (accepted: File[]) => {
    const f = accepted[0];
    if (!f) return;
    setFile(f);
    setFileText("");
    setFeatures(null);
    setResults([]);
    setComparisons({});
    setSummary("");
    setFoundCount(0);

    // Read file content
    if (f.type === "text/plain" || f.name.endsWith(".txt")) {
      const text = await f.text();
      setFileText(text);
    } else {
      // Upload to backend for PDF parsing
      const formData = new FormData();
      formData.append("file", f);
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/upload/patent`,
          { method: "POST", body: formData }
        );
        const data = await res.json();
        setFileText(data.extracted_text || "");
      } catch {
        setFileText("Failed to parse file. Please try a .txt file.");
      }
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
    },
    maxFiles: 1,
  });

  const handleAnalyze = useCallback(async () => {
    if (!fileText.trim()) return;
    setLoading(true);
    setStep("正在提取技术特征...");
    setFeatures(null);
    setResults([]);
    setComparisons({});
    setSummary("");
    setFoundCount(0);

    abortRef.current = new AbortController();

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/search/similar/stream`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: fileText, top_k: 10 }),
          signal: abortRef.current.signal,
        }
      );

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let eventType = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ") && eventType) {
            try {
              const data = JSON.parse(line.slice(6));
              handleEvent(eventType, data);
            } catch {
              // skip parse errors
            }
            eventType = "";
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setStep("分析失败，请重试");
      }
    } finally {
      setLoading(false);
    }
  }, [fileText]);

  function handleEvent(event: string, data: Record<string, unknown>) {
    switch (event) {
      case "extract_done":
        setFeatures({
          title: (data.title as string) || "",
          technical_field: (data.technical_field as string) || "",
          core_innovations: (data.core_innovations as string[]) || [],
          ipc_codes: (data.ipc_codes as string[]) || [],
          keywords: (data.keywords as string[]) || [],
          problem_statement: (data.problem_statement as string) || "",
          technical_solution: (data.technical_solution as string) || "",
        });
        break;
      case "search_start":
        setStep("正在检索相似专利...");
        break;
      case "search_progress":
        setFoundCount((data.found as number) || 0);
        setStep(`找到 ${data.found} 条相似专利`);
        break;
      case "search_results":
        const incoming = data.results as SimilarResult[];
        setResults(incoming);
        break;
      case "compare_start":
        setStep("正在进行 AI 对比分析...");
        break;
      case "comparison_result":
        const cr = data as unknown as SimilarResult & { index: number };
        setComparisons((prev) => ({
          ...prev,
          [cr.patent_number]: cr,
        }));
        setStep(`对比分析中 (${Object.keys(comparisons).length + 1}/${foundCount || results.length})...`);
        break;
      case "summary":
        setSummary((data.text as string) || "");
        break;
      case "done":
        setStep("分析完成");
        break;
    }
  }

  return (
    <div>
      <Header />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <h2 className="text-2xl font-bold text-gray-900">上传专利找相似</h2>
        <p className="mt-1 text-sm text-gray-500">
          上传专利 PDF 或文本文件，AI 将提取技术特征并检索相似专利
        </p>

        <Card className="mt-6">
          <CardContent className="pt-6">
            <div
              {...getRootProps()}
              className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors ${
                isDragActive
                  ? "border-blue-400 bg-blue-50"
                  : "border-gray-300 hover:border-gray-400"
              }`}
            >
              <input {...getInputProps()} />
              <p className="text-sm text-gray-500">
                {isDragActive ? "释放文件以上传" : "拖拽专利文档到此处，或点击选择文件"}
              </p>
              <p className="mt-1 text-xs text-gray-400">支持 PDF / TXT 格式，最大 50MB</p>
            </div>
            {file && (
              <div className="mt-4 flex items-center gap-4">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-700">{file.name}</p>
                  {fileText && (
                    <p className="text-xs text-gray-400 mt-1">
                      已提取 {fileText.length.toLocaleString()} 字符
                    </p>
                  )}
                </div>
                <Button
                  onClick={handleAnalyze}
                  disabled={loading || !fileText}
                  size="sm"
                >
                  {loading ? "分析中..." : "开始分析"}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {loading && (
          <div className="mt-4 flex items-center gap-3 text-sm text-blue-600">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
            {step}
          </div>
        )}

        {features && (
          <Card className="mt-6">
            <CardHeader><h3 className="font-semibold">提取的技术特征</h3></CardHeader>
            <CardContent>
              <div className="grid gap-3 text-sm md:grid-cols-2">
                {features.technical_field && (
                  <div>
                    <span className="text-gray-400">技术领域：</span>
                    <span>{features.technical_field}</span>
                  </div>
                )}
                {features.problem_statement && (
                  <div>
                    <span className="text-gray-400">解决问题：</span>
                    <span>{features.problem_statement}</span>
                  </div>
                )}
                {features.ipc_codes.length > 0 && (
                  <div>
                    <span className="text-gray-400">IPC 分类：</span>
                    {features.ipc_codes.map((c) => (
                      <span key={c} className="ml-1 rounded bg-gray-100 px-1.5 py-0.5 text-xs">
                        {c}
                      </span>
                    ))}
                  </div>
                )}
                {features.keywords.length > 0 && (
                  <div>
                    <span className="text-gray-400">关键词：</span>
                    <span className="text-gray-600">
                      {features.keywords.slice(0, 8).join(", ")}
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
                相似专利 ({results.length} 条)
              </h3>
              {results.map((r, i) => {
                const comp = comparisons[r.patent_number];
                return (
                  <Card key={i}>
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <span className="text-xs text-blue-600 font-mono">
                            {r.patent_number}
                          </span>
                          <h4 className="font-semibold text-gray-900 mt-1">
                            {r.title || r.patent_number}
                          </h4>
                        </div>
                        <span className="rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
                          {r.similarity_score}%
                        </span>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {r.abstract || "Loading details..."}
                      </p>
                      {comp && (
                        <div className="mt-3 space-y-2 border-t pt-3 text-xs text-gray-600">
                          {comp.tech_overlap && (
                            <p><strong className="text-gray-700">技术相似度：</strong>{comp.tech_overlap}</p>
                          )}
                          {comp.claim_overlap && (
                            <p><strong className="text-gray-700">权利要求覆盖：</strong>{comp.claim_overlap}</p>
                          )}
                          {comp.differences && (
                            <p><strong className="text-gray-700">关键差异：</strong>{comp.differences}</p>
                          )}
                          {comp.comparison && !comp.tech_overlap && (
                            <p>{comp.comparison}</p>
                          )}
                        </div>
                      )}
                      <div className="mt-3 flex flex-wrap gap-2">
                        {r.ipc_codes?.map((code) => (
                          <span key={code} className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                            {code}
                          </span>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            <div className="space-y-4">
              {summary && (
                <Card>
                  <CardHeader><h3 className="font-semibold">AI 分析总结</h3></CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 whitespace-pre-wrap">{summary}</p>
                  </CardContent>
                </Card>
              )}

              {results.length > 0 && (
                <Card>
                  <CardHeader><h3 className="font-semibold">相似度排行</h3></CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {results.slice(0, 8).map((r, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm">
                          <span className="w-6 text-right text-xs text-gray-400">{i + 1}</span>
                          <span className="truncate flex-1 text-xs font-mono text-gray-600">
                            {r.patent_number}
                          </span>
                          <div className="w-24">
                            <div className="h-2 rounded-full bg-gray-100">
                              <div
                                className="h-2 rounded-full bg-blue-500"
                                style={{ width: `${Math.min(r.similarity_score, 100)}%` }}
                              />
                            </div>
                          </div>
                          <span className="w-10 text-right text-xs text-gray-500">
                            {r.similarity_score}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
