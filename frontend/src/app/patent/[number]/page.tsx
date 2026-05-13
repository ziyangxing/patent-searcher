"use client";

import { Header } from "@/components/Header";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useParams } from "next/navigation";
import { useState, useRef, useCallback } from "react";

export default function PatentDetailPage() {
  const { number } = useParams<{ number: string }>();
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [patentInfo, setPatentInfo] = useState<Record<string, string> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const handleSend = useCallback(async () => {
    if (!input.trim()) return;
    const question = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setLoading(true);

    abortRef.current = new AbortController();

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/chat/patent/${encodeURIComponent(number)}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: question }),
          signal: abortRef.current.signal,
        }
      );

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");
      const decoder = new TextDecoder();
      let buffer = "";
      let aiText = "";

      setMessages((prev) => [...prev, { role: "ai", text: "" }]);

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
              if (eventType === "patent_loaded") {
                setPatentInfo(data);
              } else if (eventType === "answer_chunk" && data.text) {
                aiText += data.text;
                setMessages((prev) => {
                  const copy = [...prev];
                  copy[copy.length - 1] = { role: "ai", text: aiText };
                  return copy;
                });
              }
            } catch {
              // skip parse errors
            }
            eventType = "";
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setMessages((prev) => [
          ...prev,
          { role: "ai", text: "Sorry, failed to get a response. Please try again." },
        ]);
      }
    } finally {
      setLoading(false);
    }
  }, [input, number]);

  return (
    <div>
      <Header />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <h2 className="text-2xl font-bold text-gray-900">专利详情</h2>
        <p className="mt-1 font-mono text-sm text-blue-600">{decodeURIComponent(number)}</p>

        {patentInfo && (
          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader><h3 className="font-semibold">基本信息</h3></CardHeader>
              <CardContent>
                <dl className="space-y-2 text-sm">
                  <div className="flex gap-2">
                    <dt className="text-gray-400 w-20 shrink-0">标题</dt>
                    <dd className="text-gray-700">{patentInfo.title}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-gray-400 w-20 shrink-0">IPC</dt>
                    <dd className="text-gray-700">{patentInfo.ipc_codes}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-gray-400 w-20 shrink-0">申请人</dt>
                    <dd className="text-gray-700">{patentInfo.applicants}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-gray-400 w-20 shrink-0">日期</dt>
                    <dd className="text-gray-700">{patentInfo.pub_date}</dd>
                  </div>
                </dl>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><h3 className="font-semibold">摘要</h3></CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">{patentInfo.abstract || "No abstract available"}</p>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="mt-8">
          <Card>
            <CardHeader><h3 className="font-semibold">AI 专利问答</h3></CardHeader>
            <CardContent>
              <div className="h-80 overflow-y-auto space-y-3 mb-4 rounded-lg bg-gray-50 p-4">
                {messages.length === 0 && (
                  <p className="text-sm text-gray-400 text-center pt-20">
                    Ask questions about this patent — the AI will answer based on the patent content.
                  </p>
                )}
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`text-sm ${msg.role === "user" ? "text-right" : "text-left"}`}
                  >
                    <span
                      className={`inline-block rounded-lg px-3 py-2 max-w-[80%] ${
                        msg.role === "user"
                          ? "bg-blue-600 text-white"
                          : "bg-white border border-gray-200 text-gray-700"
                      }`}
                    >
                      {msg.text || (loading && msg.role === "ai" ? "Thinking..." : "")}
                    </span>
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  placeholder="Ask about this patent..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  disabled={loading}
                />
                <Button onClick={handleSend} disabled={loading || !input.trim()} size="sm">
                  {loading ? "..." : "Send"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
