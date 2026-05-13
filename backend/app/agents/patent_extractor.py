import json
from dataclasses import dataclass, field
from app.services.llm import llm_service


@dataclass
class PatentFeatures:
    title: str = ""
    technical_field: str = ""
    core_innovations: list[str] = field(default_factory=list)
    ipc_codes: list[str] = field(default_factory=list)
    cpc_codes: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    search_queries: list[str] = field(default_factory=list)
    independent_claims_summary: str = ""
    problem_statement: str = ""
    technical_solution: str = ""


EXTRACT_PROMPT = """You are a patent examiner. Analyze the following patent document and extract structured information.

Patent text:
{text}

Return ONLY a JSON object with these fields:
- "title": The patent title (inferred from content if not explicit)
- "technical_field": Broad technical domain (1 sentence)
- "core_innovations": Key innovative features (list of 3-5 strings)
- "ipc_codes": Predicted IPC classification codes (list of 2-5 codes like "G06V20/58")
- "cpc_codes": Predicted CPC codes if possible
- "keywords": Important technical keywords including synonyms (list of 8-15 strings)
- "search_queries": Optimized search queries for finding similar patents (list of 3-5 strings, each 5-15 words, covering different aspects)
- "independent_claims_summary": Brief summary of independent claims (1-2 sentences)
- "problem_statement": What problem does this invention solve? (1 sentence)
- "technical_solution": How does it solve the problem? (1-2 sentences)

JSON:"""


class PatentExtractor:
    def __init__(self):
        self.llm = llm_service

    async def extract(self, text: str) -> PatentFeatures:
        """Extract structured patent features from document text."""
        truncated = text[:8000]

        try:
            prompt = EXTRACT_PROMPT.format(text=truncated)
            response = await self.llm.complete(
                prompt=prompt,
                system_prompt="You are a patent examiner. Always return valid JSON.",
                temperature=0.1,
                max_tokens=1500,
            )

            data = self._parse_json(response)
            return PatentFeatures(
                title=data.get("title", ""),
                technical_field=data.get("technical_field", ""),
                core_innovations=data.get("core_innovations", []),
                ipc_codes=data.get("ipc_codes", []),
                cpc_codes=data.get("cpc_codes", []),
                keywords=data.get("keywords", []),
                search_queries=data.get("search_queries", []),
                independent_claims_summary=data.get("independent_claims_summary", ""),
                problem_statement=data.get("problem_statement", ""),
                technical_solution=data.get("technical_solution", ""),
            )
        except Exception:
            return self._fallback_extract(text)

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text)

    def _fallback_extract(self, text: str) -> PatentFeatures:
        """Basic keyword extraction without LLM."""
        import re

        STOP_WORDS = {
            "the", "and", "for", "that", "this", "with", "from", "are", "has",
            "been", "can", "its", "not", "also", "one", "two", "may", "said",
            "each", "any", "will", "more", "such", "into", "than", "when",
            "which", "have", "other", "some", "these", "those", "about",
            "method", "system", "apparatus", "device", "comprising", "claim",
            "claims", "invention", "present", "including", "includes",
            "wherein", "thereof", "thereby", "herein", "therein",
            "a", "an", "is", "of", "in", "to", "it", "be", "as", "at",
            "by", "on", "or", "no", "if", "so", "we", "he", "she", "they",
        }

        words = re.findall(r"[a-zA-Z一-鿿]{3,}", text[:3000])
        word_freq: dict[str, int] = {}
        for w in words:
            wl = w.lower()
            if wl in STOP_WORDS or len(w) < 4:
                continue
            word_freq[wl] = word_freq.get(wl, 0) + 1
        top_keywords = sorted(word_freq, key=word_freq.get, reverse=True)[:15]

        return PatentFeatures(
            keywords=top_keywords,
            search_queries=[" ".join(top_keywords[:8])],
            technical_field="",
        )


patent_extractor = PatentExtractor()
