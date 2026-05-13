import asyncio
from dataclasses import dataclass, field
from app.services.llm import llm_service
from app.search.elasticsearch import es_client
from app.search.faiss_index import faiss_manager
from app.search.patent_provider import google_patents
from app.services.embedding import embedding_service


@dataclass
class SearchPlan:
    original_query: str
    expanded_queries: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    ipc_codes: list[str] = field(default_factory=list)
    technical_field: str = ""
    core_features: list[str] = field(default_factory=list)


@dataclass
class SearchResult:
    patent_number: str
    title: str
    abstract: str
    score: float
    source: str  # "keyword" or "semantic"
    ipc_codes: list[str] = field(default_factory=list)
    applicants: list[str] = field(default_factory=list)
    publication_date: str = ""


INTENT_PARSE_PROMPT = """You are a patent search expert. Analyze the user's invention description and extract structured search parameters.

Return ONLY a JSON object with these fields:
- "technical_field": The broad technical domain (1 sentence)
- "core_features": Key technical features (list of 3-5 strings)
- "keywords": Search keywords including synonyms and alternative terms (list of 5-10 strings)
- "ipc_codes": Predicted IPC classification codes (list of 2-5 codes like "G06V20/58")
- "expanded_queries": Alternative search queries capturing different aspects (list of 2-3 strings)

User query: {query}

JSON:"""


RANKING_PROMPT = """You are a patent examiner. Score the relevance of each patent to the user's query on a scale of 0-100.

User query: {query}

Technical field: {field}
Core features: {features}

Patents to score:
{patents}

Return ONLY a JSON array of objects with "patent_number" and "score" (0-100 integer):
[{{"patent_number": "CN110123456A", "score": 95}}, ...]
"""


class SearchAgent:
    def __init__(self):
        self.llm = llm_service

    async def parse_intent(self, query: str) -> SearchPlan:
        """Step 1: LLM parses user intent into structured search parameters."""
        import json

        try:
            prompt = INTENT_PARSE_PROMPT.format(query=query)
            response = await self.llm.complete(
                prompt=prompt,
                system_prompt="You are a patent search expert. Always return valid JSON.",
                temperature=0.1,
            )
            # Extract JSON from response
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            data = json.loads(text)
            return SearchPlan(
                original_query=query,
                expanded_queries=data.get("expanded_queries", []),
                keywords=data.get("keywords", []),
                ipc_codes=data.get("ipc_codes", []),
                technical_field=data.get("technical_field", ""),
                core_features=data.get("core_features", []),
            )
        except Exception:
            # Fallback: use basic keyword extraction
            return SearchPlan(
                original_query=query,
                expanded_queries=[query],
                keywords=query.split(),
                technical_field="",
                core_features=[],
            )

    async def hybrid_search(
        self, plan: SearchPlan, top_k: int = 20
    ) -> list[SearchResult]:
        """Step 2: Multi-source search — Google Patents (primary) + FAISS (secondary)."""
        seen_ids = set()
        all_results = []

        # Primary: Google Patents (real global patents, free, no API key needed)
        search_query = plan.original_query
        if plan.expanded_queries:
            search_query = plan.expanded_queries[0]

        try:
            google_results = await google_patents.search(search_query, num=top_k)
            for r in google_results:
                pn = r.get("patent_number", "")
                if pn and pn not in seen_ids:
                    seen_ids.add(pn)
                    all_results.append(
                        SearchResult(
                            patent_number=pn,
                            title=r.get("title", ""),
                            abstract=r.get("abstract", ""),
                            score=r.get("similarity_score", 50) / 100.0,
                            source="google_patents",
                            ipc_codes=r.get("ipc_codes", []),
                            applicants=r.get("applicants", []),
                            publication_date=r.get("publication_date", ""),
                        )
                    )
        except Exception:
            pass

        # Secondary: Local FAISS semantic search
        try:
            if faiss_manager.index is not None and faiss_manager.size > 0:
                faiss_results = faiss_manager.search(plan.original_query, k=min(top_k, faiss_manager.size))
                for patent_id, score in faiss_results:
                    if patent_id not in seen_ids:
                        seen_ids.add(patent_id)
                        all_results.append(
                            SearchResult(
                                patent_number=patent_id,
                                title="",
                                abstract="",
                                score=score,
                                source="faiss",
                            )
                        )
        except Exception:
            pass

        return all_results[:top_k]

    def _rrf_fusion(
        self,
        list_a: list[SearchResult],
        list_b: list[SearchResult],
        k: int = 60,
    ) -> list[SearchResult]:
        """Reciprocal Rank Fusion: merge two ranked lists."""
        scores: dict[str, float] = {}
        results: dict[str, SearchResult] = {}

        for rank, r in enumerate(list_a, start=1):
            scores[r.patent_number] = scores.get(r.patent_number, 0) + 1 / (k + rank)
            results[r.patent_number] = r

        for rank, r in enumerate(list_b, start=1):
            scores[r.patent_number] = scores.get(r.patent_number, 0) + 1 / (k + rank)
            if r.patent_number not in results:
                results[r.patent_number] = r

        merged = sorted(
            results.values(),
            key=lambda x: scores.get(x.patent_number, 0),
            reverse=True,
        )
        for r in merged:
            r.score = scores.get(r.patent_number, 0)
        return merged

    async def rerank_with_llm(
        self,
        query: str,
        plan: SearchPlan,
        candidates: list[SearchResult],
    ) -> list[SearchResult]:
        """Step 3: LLM-based re-ranking for fine-grained relevance."""
        if not candidates:
            return []

        patent_list = []
        for i, r in enumerate(candidates[:20]):
            patent_list.append(
                f"{i+1}. [{r.patent_number}] {r.title[:80]}\n   {r.abstract[:120]}"
            )

        import json

        try:
            prompt = RANKING_PROMPT.format(
                query=query,
                field=plan.technical_field,
                features=", ".join(plan.core_features),
                patents="\n".join(patent_list),
            )
            response = await self.llm.complete(
                prompt=prompt,
                system_prompt="You are a patent examiner. Always return valid JSON array.",
                temperature=0.1,
            )
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            scores = json.loads(text)
            score_map = {s["patent_number"]: s["score"] / 100.0 for s in scores}

            for r in candidates:
                r.score = score_map.get(r.patent_number, r.score)

            candidates.sort(key=lambda x: x.score, reverse=True)
        except Exception:
            pass

        return candidates

    async def generate_analysis(
        self, query: str, plan: SearchPlan, results: list[SearchResult]
    ) -> str:
        """Step 4: Generate AI analysis of search results."""
        if not results:
            return "No relevant patents found."

        top_patents = []
        for r in results[:5]:
            top_patents.append(
                f"- [{r.patent_number}] {r.title} (score: {r.score:.2f})"
            )

        prompt = f"""Analyze the following patent search results for the query: "{query}"

Technical field: {plan.technical_field}
Core features: {", ".join(plan.core_features)}

Top results:
{chr(10).join(top_patents)}

Provide a concise analysis covering:
1. Technology landscape overview (1-2 sentences)
2. Key players/applicants identified
3. Main IPC classification areas
4. Recommendation for further search refinement

Keep it under 200 words."""

        try:
            response = await self.llm.complete(
                prompt=prompt,
                system_prompt="You are a patent analyst. Provide concise, factual analysis.",
                temperature=0.3,
                max_tokens=300,
            )
            return response.strip()
        except Exception:
            return "Analysis unavailable. Please review the results above."

    async def search(self, query: str, top_k: int = 5) -> dict:
        """Full search pipeline: intent → search → rerank → analyze."""
        plan = await self.parse_intent(query)
        candidates = await self.hybrid_search(plan, top_k)
        ranked = await self.rerank_with_llm(query, plan, candidates)
        analysis = await self.generate_analysis(query, plan, ranked)

        return {
            "plan": {
                "technical_field": plan.technical_field,
                "core_features": plan.core_features,
                "keywords": plan.keywords,
                "ipc_codes": plan.ipc_codes,
                "expanded_queries": plan.expanded_queries,
            },
            "results": [
                {
                    "patent_number": r.patent_number,
                    "title": r.title,
                    "abstract": r.abstract,
                    "similarity_score": round(r.score * 100, 1),
                    "source": r.source,
                    "ipc_codes": r.ipc_codes,
                    "applicants": r.applicants,
                    "publication_date": r.publication_date,
                }
                for r in ranked[:top_k]
            ],
            "analysis": analysis,
            "total": len(ranked),
        }


search_agent = SearchAgent()
