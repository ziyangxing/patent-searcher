"""
Multi-source patent search: Google Patents, Espacenet, Lens.org, WIPO.
Searches all enabled sources in parallel, deduplicates, and merges results.
"""
import re
import asyncio
import httpx
from abc import ABC, abstractmethod
from urllib.parse import quote, urlencode

# ============================================================
# Base Provider
# ============================================================


class PatentResult:
    __slots__ = (
        "patent_number", "title", "abstract", "source", "score",
        "publication_date", "applicants", "inventors",
        "google_url", "espacenet_url", "pdf_url",
    )

    def __init__(self, patent_number="", title="", abstract="", source="", score=0.0):
        self.patent_number = patent_number
        self.title = title
        self.abstract = abstract
        self.source = source
        self.score = score
        self.publication_date = ""
        self.applicants = []
        self.inventors = []
        self.google_url = f"https://patents.google.com/patent/{patent_number}/en"
        self.espacenet_url = f"https://worldwide.espacenet.com/patent/search?q=pn%3D{patent_number}"
        self.pdf_url = ""

    def to_dict(self):
        return {
            "patent_number": self.patent_number,
            "title": self.title,
            "abstract": self.abstract,
            "source": self.source,
            "similarity_score": round(self.score * 100, 1),
            "publication_date": self.publication_date,
            "applicants": self.applicants,
            "inventors": self.inventors,
            "google_url": self.google_url,
            "espacenet_url": self.espacenet_url,
        }


class BaseProvider(ABC):
    name = "base"

    @abstractmethod
    async def search(self, query: str, num: int = 20) -> list[PatentResult]:
        pass

    @abstractmethod
    async def get_detail(self, patent_number: str) -> dict | None:
        pass

    @abstractmethod
    async def get_pdf_url(self, patent_number: str) -> str | None:
        pass


# ============================================================
# Google Patents (via SerpAPI)
# ============================================================


class GooglePatentsProvider(BaseProvider):
    name = "google_patents"

    def __init__(self, serpapi_key: str = ""):
        self.serpapi_key = serpapi_key

    async def search(self, query: str, num: int = 20) -> list[PatentResult]:
        if not self.serpapi_key:
            return []
        try:
            params = {
                "engine": "google_patents",
                "q": query,
                "api_key": self.serpapi_key,
                "num": max(num, 10),
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get("https://serpapi.com/search", params=params)
                data = resp.json()
                if "error" in data:
                    return []

                results = []
                for i, r in enumerate(data.get("organic_results", [])[:num]):
                    pn = r.get("publication_number", "")
                    if not pn:
                        continue
                    pr = PatentResult(pn, r.get("title", ""), r.get("snippet", "")[:500], self.name)
                    pr.score = max(50, 95 - i * 3) / 100.0
                    pr.publication_date = r.get("publication_date", "")
                    pr.applicants = [r.get("assignee", "")] if r.get("assignee") else []
                    pr.inventors = [r.get("inventor", "")] if r.get("inventor") else []
                    results.append(pr)
                return results
        except Exception:
            return []

    async def get_detail(self, patent_number: str) -> dict | None:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"https://patents.google.com/patent/{patent_number}/en",
                    headers=headers,
                )
                if resp.status_code != 200:
                    return None
                return self._parse_html(resp.text, patent_number)
        except Exception:
            return None

    async def get_pdf_url(self, patent_number: str) -> str | None:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(
                    f"https://patents.google.com/patent/{patent_number}/en",
                    headers=headers,
                )
                urls = re.findall(
                    r"https://patentimages\.storage\.googleapis\.com/[^\"'\s]+\.pdf",
                    resp.text,
                )
                return urls[0] if urls else None
        except Exception:
            return None

    def _parse_html(self, html: str, pn: str) -> dict:
        title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL)
        title = re.sub(r"<[^>]+>", "", title_m.group(1)).replace(" - Google Patents", "").strip() if title_m else pn
        abstract_m = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
        abstract = abstract_m.group(1)[:500] if abstract_m else ""
        assignee_m = re.search(r'<dd[^>]*itemprop="assignee"[^>]*>(.*?)</dd>', html, re.DOTALL)
        applicants = [re.sub(r"<[^>]+>", "", assignee_m.group(1)).strip()] if assignee_m else []
        return {"patent_number": pn, "title": title, "abstract": abstract, "applicants": applicants}


# ============================================================
# Espacenet (European Patent Office) - Free, no key needed
# ============================================================


class EspacenetProvider(BaseProvider):
    name = "espacenet"

    async def search(self, query: str, num: int = 20) -> list[PatentResult]:
        try:
            headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
            params = {"q": f"ti all \"{query}\"", "range": f"1-{min(num, 30)}"}
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://worldwide.espacenet.com/3.2/rest-services/rest/patent/publications/search",
                    params=params,
                    headers=headers,
                )
                if resp.status_code != 200:
                    return []
                data = resp.json()
                docs = (
                    data.get("ops:world-patent-data", {})
                    .get("ops:biblio-search", {})
                    .get("ops:search-result", {})
                    .get("ops:publication-reference", [])
                )
                if isinstance(docs, dict):
                    docs = [docs]

                results = []
                for i, doc in enumerate(docs[:num]):
                    did = doc.get("document-id", {})
                    if isinstance(did, list):
                        did = did[0]
                    pn = f"{did.get('country', '')}{did.get('doc-number', '')}{did.get('kind', '')}"
                    if not pn:
                        continue
                    pr = PatentResult(pn, "", "", self.name)
                    pr.score = max(50, 90 - i * 3) / 100.0
                    results.append(pr)
                return results
        except Exception:
            return []

    async def get_detail(self, patent_number: str) -> dict | None:
        return None

    async def get_pdf_url(self, patent_number: str) -> str | None:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            url = f"https://worldwide.espacenet.com/patent/search?q=pn%3D{patent_number}"
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                pdf_urls = re.findall(
                    r"https://[^\"'\s]*OriginalDocument[^\"'\s]*\.pdf",
                    resp.text,
                )
                return pdf_urls[0] if pdf_urls else None
        except Exception:
            return None


# ============================================================
# Lens.org - Free scholarly patent search
# ============================================================


class LensProvider(BaseProvider):
    name = "lens"

    async def search(self, query: str, num: int = 20) -> list[PatentResult]:
        try:
            headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
            params = {"q": query, "size": min(num, 50)}
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://api.lens.org/scholarly/search",
                    params=params,
                    headers=headers,
                )
                if resp.status_code != 200:
                    return []
                data = resp.json()
                hits = data.get("results", data.get("data", []))
                results = []
                for i, r in enumerate(hits[:num]):
                    pn = r.get("publication_number", r.get("id", ""))
                    if not pn:
                        continue
                    title = r.get("title", "")
                    abstract = r.get("abstract", r.get("snippet", ""))[:500]
                    pr = PatentResult(str(pn), title, abstract, self.name)
                    pr.score = max(50, 88 - i * 3) / 100.0
                    if r.get("date"):
                        pr.publication_date = str(r["date"])
                    results.append(pr)
                return results
        except Exception:
            return []

    async def get_detail(self, patent_number: str) -> dict | None:
        return None

    async def get_pdf_url(self, patent_number: str) -> str | None:
        return None


# ============================================================
# Multi-Source Orchestrator
# ============================================================


class MultiSourceSearcher:
    def __init__(self, serpapi_key: str = ""):
        self.providers: list[BaseProvider] = [
            GooglePatentsProvider(serpapi_key),
            EspacenetProvider(),
            LensProvider(),
        ]

    async def search_all(self, query: str, num: int = 20) -> list[PatentResult]:
        """Search all providers in parallel, deduplicate, merge, rank."""
        tasks = [p.search(query, num) for p in self.providers]
        all_results_lists = await asyncio.gather(*tasks, return_exceptions=True)

        seen = {}
        merged = []
        for results in all_results_lists:
            if isinstance(results, Exception):
                continue
            for r in results:
                pn = r.patent_number
                if pn and pn not in seen:
                    seen[pn] = r
                    merged.append(r)

        merged.sort(key=lambda x: x.score, reverse=True)
        return merged[:num]

    async def get_all_details(self, patent_number: str) -> dict:
        """Get patent detail from all sources, return merged result."""
        for provider in self.providers:
            try:
                detail = await provider.get_detail(patent_number)
                if detail and detail.get("title"):
                    return detail
            except Exception:
                continue
        return {"patent_number": patent_number, "title": patent_number, "abstract": "", "applicants": []}

    async def get_pdf_url(self, patent_number: str) -> str | None:
        """Try all providers for PDF URL."""
        for provider in self.providers:
            try:
                url = await provider.get_pdf_url(patent_number)
                if url:
                    return url
            except Exception:
                continue
        return None

    async def download_pdf(self, patent_number: str, save_dir: str = "./downloads") -> str | None:
        """Download patent PDF via best available source."""
        import os
        os.makedirs(save_dir, exist_ok=True)

        pdf_url = await self.get_pdf_url(patent_number)
        if not pdf_url:
            return None

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                resp = await client.get(pdf_url, headers=headers)
                if resp.status_code == 200 and resp.content[:4] == b"%PDF":
                    path = os.path.join(save_dir, f"{patent_number}.pdf")
                    with open(path, "wb") as f:
                        f.write(resp.content)
                    return path
        except Exception:
            pass
        return None
