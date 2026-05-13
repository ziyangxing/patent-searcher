import json
from dataclasses import dataclass, field
from app.services.llm import llm_service
from app.services.embedding import embedding_service
from app.search.faiss_index import faiss_manager
from app.agents.patent_extractor import PatentFeatures


@dataclass
class SimilarPatentResult:
    patent_number: str
    title: str
    abstract: str
    similarity_score: float
    ipc_codes: list[str] = field(default_factory=list)
    applicants: list[str] = field(default_factory=list)
    publication_date: str = ""
    comparison: str = ""
    tech_overlap: str = ""
    claim_overlap: str = ""
    differences: str = ""


COMPARISON_PROMPT = """You are a patent examiner. Compare the uploaded patent with a found similar patent.

Uploaded Patent:
- Title: {source_title}
- Technical Field: {source_field}
- Core Innovations: {source_innovations}
- Problem: {source_problem}
- Solution: {source_solution}

Found Patent:
- Number: {target_number}
- Title: {target_title}
- Abstract: {target_abstract}

Provide a concise comparison covering:
1. Technical similarity: How similar are the technical approaches? (1-2 sentences)
2. Innovation overlap: Do they share core innovations? (1-2 sentences)
3. Claim scope: Would claims potentially overlap? (1 sentence)
4. Key differences: What distinguishes them? (1-2 sentences)

Keep the total under 150 words."""


class SimilarityAgent:
    def __init__(self):
        self.llm = llm_service

    async def search_similar(
        self,
        features: PatentFeatures,
        source_text: str,
        top_k: int = 10,
        threshold: float = 0.3,
    ) -> list[SimilarPatentResult]:
        """Search for similar patents using multi-query semantic search."""

        results: dict[str, SimilarPatentResult] = {}

        # Build search queries
        queries = [features.technical_solution] if features.technical_solution else []
        queries.extend(features.search_queries)
        queries.extend(features.keywords[:5])
        if not queries:
            queries = [source_text[:500]]

        # Run FAISS search for each query
        for query in queries[:5]:
            if not query.strip():
                continue
            try:
                if faiss_manager.index is not None:
                    hits = faiss_manager.search(query, k=top_k)
                    for patent_id, score in hits:
                        if score < threshold:
                            continue
                        if patent_id not in results or score > results[patent_id].similarity_score:
                            results[patent_id] = SimilarPatentResult(
                                patent_number=patent_id,
                                title="",
                                abstract="",
                                similarity_score=round(score, 4),
                            )
            except Exception:
                pass

        # Sort and limit
        sorted_results = sorted(
            results.values(), key=lambda x: x.similarity_score, reverse=True
        )
        return sorted_results[:top_k]

    async def compare_patents(
        self,
        features: PatentFeatures,
        similar_patents: list[SimilarPatentResult],
    ) -> list[SimilarPatentResult]:
        """AI-powered comparison between source patent and each similar patent."""

        innovations = ", ".join(features.core_innovations[:5]) or "Not specified"

        for patent in similar_patents:
            try:
                prompt = COMPARISON_PROMPT.format(
                    source_title=features.title or "Uploaded Patent",
                    source_field=features.technical_field or "Not specified",
                    source_innovations=innovations,
                    source_problem=features.problem_statement or "Not specified",
                    source_solution=features.technical_solution or "Not specified",
                    target_number=patent.patent_number,
                    target_title=patent.title or patent.patent_number,
                    target_abstract=patent.abstract or "Not available",
                )

                response = await self.llm.complete(
                    prompt=prompt,
                    system_prompt="You are a patent examiner. Provide concise comparisons.",
                    temperature=0.2,
                    max_tokens=400,
                )

                patent.comparison = response.strip()
                self._parse_comparison_sections(patent, response)
            except Exception:
                patent.comparison = (
                    f"Similarity score: {patent.similarity_score:.0%}. "
                    "Configure LLM API key for detailed comparison."
                )

        return similar_patents

    def _parse_comparison_sections(self, patent: SimilarPatentResult, text: str):
        """Extract structured sections from comparison text."""
        lines = text.split("\n")
        current_section = ""
        sections: dict[str, str] = {}

        for line in lines:
            line_lower = line.lower().strip()
            if "technical similarity" in line_lower or "technical approach" in line_lower:
                current_section = "tech"
            elif "innovation overlap" in line_lower or "core innovation" in line_lower:
                current_section = "innovation"
            elif "claim" in line_lower and ("scope" in line_lower or "overlap" in line_lower):
                current_section = "claim"
            elif "difference" in line_lower or "distinguish" in line_lower:
                current_section = "diff"
            elif line.strip() and current_section:
                sections[current_section] = sections.get(current_section, "") + " " + line.strip()

        patent.tech_overlap = sections.get("tech", "").strip()[:200]
        patent.claim_overlap = sections.get("claim", "").strip()[:200]
        patent.differences = sections.get("diff", "").strip()[:200]

    async def generate_summary(
        self,
        features: PatentFeatures,
        results: list[SimilarPatentResult],
    ) -> str:
        """Generate overall analysis summary."""

        if not results:
            return "No similar patents found in the current database. Try expanding your search or adding more patent data."

        top_list = "\n".join(
            f"- {r.patent_number}: score={r.similarity_score:.0%}"
            for r in results[:5]
        )

        prompt = f"""Summarize the similarity search results for a patent with these features:
- Technical field: {features.technical_field}
- Core innovations: {', '.join(features.core_innovations[:5])}

Top similar patents found:
{top_list}

Provide a brief summary (under 100 words) covering:
1. Whether close prior art exists
2. The general technology landscape
3. Recommendation for the user"""

        try:
            response = await self.llm.complete(
                prompt=prompt,
                system_prompt="You are a patent analyst. Be concise and factual.",
                temperature=0.3,
                max_tokens=250,
            )
            return response.strip()
        except Exception:
            if results:
                top = results[0]
                return (
                    f"Most similar patent found: {top.patent_number} "
                    f"(similarity: {top.similarity_score:.0%}). "
                    f"Configure LLM API key for detailed analysis."
                )
            return "No similar patents found."

    async def run_full_pipeline(
        self,
        text: str,
        features: PatentFeatures,
        top_k: int = 10,
    ) -> dict:
        """Full similarity search and comparison pipeline."""

        # Step 1: Semantic search
        candidates = await self.search_similar(features, text, top_k)

        # Step 2: AI comparison
        compared = await self.compare_patents(features, candidates)

        # Step 3: Summary
        summary = await self.generate_summary(features, compared)

        return {
            "source_features": {
                "title": features.title,
                "technical_field": features.technical_field,
                "core_innovations": features.core_innovations,
                "ipc_codes": features.ipc_codes,
                "problem_statement": features.problem_statement,
                "technical_solution": features.technical_solution,
            },
            "results": [
                {
                    "patent_number": r.patent_number,
                    "title": r.title,
                    "abstract": r.abstract,
                    "similarity_score": round(r.similarity_score * 100, 1),
                    "comparison": r.comparison,
                    "tech_overlap": r.tech_overlap,
                    "claim_overlap": r.claim_overlap,
                    "differences": r.differences,
                    "ipc_codes": r.ipc_codes,
                    "applicants": r.applicants,
                }
                for r in compared
            ],
            "summary": summary,
            "total": len(compared),
        }


similarity_agent = SimilarityAgent()
