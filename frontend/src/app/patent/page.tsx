"use client";

import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function PatentNumberPage() {
  const [number, setNumber] = useState("");
  const router = useRouter();

  const handleSearch = () => {
    if (number.trim()) router.push(`/patent/${encodeURIComponent(number.trim())}`);
  };

  return (
    <div>
      <Header />
      <main className="mx-auto max-w-3xl px-4 py-8">
        <h2 className="text-2xl font-bold text-gray-900">专利号精准检索</h2>
        <p className="mt-1 text-sm text-gray-500">
          支持 CN / US / EP / WO / JP 等主要国家/地区的专利号格式
        </p>
        <div className="mt-6 flex gap-3">
          <Input
            placeholder="输入专利号，如 CN110123456A"
            value={number}
            onChange={(e) => setNumber(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="flex-1"
          />
          <Button size="lg" onClick={handleSearch}>
            检索
          </Button>
        </div>
      </main>
    </div>
  );
}
