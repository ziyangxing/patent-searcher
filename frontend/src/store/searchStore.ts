import { create } from "zustand";

export interface PatentResult {
  patent_number: string;
  title: string;
  abstract: string;
  similarity_score?: number;
  ipc_codes?: string[];
  applicants?: string[];
  publication_date?: string;
  google_url?: string;
  espacenet_url?: string;
}

export interface SearchState {
  query: string;
  results: PatentResult[];
  isLoading: boolean;
  activeTab: "intent" | "number" | "upload";
  setQuery: (q: string) => void;
  setResults: (results: PatentResult[]) => void;
  setLoading: (v: boolean) => void;
  setActiveTab: (tab: "intent" | "number" | "upload") => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  query: "",
  results: [],
  isLoading: false,
  activeTab: "intent",
  setQuery: (query) => set({ query }),
  setResults: (results) => set({ results }),
  setLoading: (isLoading) => set({ isLoading }),
  setActiveTab: (activeTab) => set({ activeTab }),
}));
