"""Real patent search providers: Google Patents (via SerpAPI) + EPO OPS."""

import json
import httpx
from app.core.config import settings


class GooglePatentsProvider:
    """Search Google Patents via SerpAPI for real global patent results."""

    BASE = "https://serpapi.com/search"

    async def search(
        self, query: str, num: int = 20, language: str = "EN"
    ) -> list[dict]:
        """Search Google Patents via SerpAPI. Returns real patent results."""
        num = max(num, 10)  # SerpAPI requires num >= 10

        # Try SerpAPI first (free key at https://serpapi.com)
        if settings.SERPAPI_KEY:
            results = await self._search_serpapi(query, num, language)
            if results:
                return results
            # If SerpAPI key is set but returns empty, don't fall back
            return []

        # No API key — return empty with clear message
        # User needs to get a free key from https://serpapi.com
        return []

    async def _search_serpapi(
        self, query: str, num: int, language: str
    ) -> list[dict]:
        try:
            params = {
                "engine": "google_patents",
                "q": query,
                "api_key": settings.SERPAPI_KEY,
                "num": min(num, 100),
                "hl": language.lower(),
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(self.BASE, params=params)
                if resp.status_code != 200:
                    return []

                data = resp.json()
                results = []
                for i, r in enumerate(data.get("organic_results", [])[:num]):
                    patent_number = r.get("publication_number", "")
                    if not patent_number:
                        continue
                    results.append(
                        {
                            "patent_number": patent_number,
                            "title": r.get("title", ""),
                            "abstract": r.get("snippet", "")[:500],
                            "ipc_codes": [],
                            "applicants": [r.get("assignee", "")] if r.get("assignee") else [],
                            "inventors": [r.get("inventor", "")] if r.get("inventor") else [],
                            "publication_date": r.get("publication_date", ""),
                            "filing_date": r.get("filing_date", ""),
                            "google_url": f"https://patents.google.com/patent/{patent_number}/en",
                            "espacenet_url": f"https://worldwide.espacenet.com/patent/search?q=pn%3D{patent_number}",
                            "source": "google_patents",
                            "similarity_score": max(50, 95 - i * 3),
                        }
                    )
                return results
        except Exception:
            return []

    async def _search_direct(
        self, query: str, num: int, language: str
    ) -> list[dict]:
        """Direct Google Patents search (fallback, no API key needed)."""
        try:
            import re
            from urllib.parse import quote

            url = f"https://patents.google.com/?q={quote(query)}&language={language}&num={num}"
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; PatentSearch/1.0)"
            }

            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return []

                html = resp.text
                results = []

                # Parse patent results from HTML
                patent_pattern = re.compile(
                    r'<a[^>]*href="[^"]*patent/([A-Z]{2}\d+[A-Z]\d?)[^"]*"[^>]*>(.*?)</a>',
                    re.DOTALL,
                )
                snippet_pattern = re.compile(
                    r'<div[^>]*class="[^"]*snippet[^"]*"[^>]*>(.*?)</div>',
                    re.DOTALL,
                )

                patents = patent_pattern.findall(html)
                snippets = snippet_pattern.findall(html)

                seen = set()
                for i, (pn, title_html) in enumerate(patents[:num]):
                    pn = pn.strip()
                    if pn in seen:
                        continue
                    seen.add(pn)
                    title = re.sub(r"<[^>]+>", "", title_html).strip()
                    snippet = snippets[i] if i < len(snippets) else ""
                    snippet = re.sub(r"<[^>]+>", "", snippet).strip()

                    results.append(
                        {
                            "patent_number": pn,
                            "title": title[:200],
                            "abstract": snippet[:500],
                            "ipc_codes": [],
                            "applicants": [],
                            "publication_date": "",
                            "google_url": f"https://patents.google.com/patent/{pn}/en",
                            "espacenet_url": f"https://worldwide.espacenet.com/patent/search?q=pn%3D{pn}",
                            "source": "google_patents",
                            "similarity_score": 100 - (i * 3),
                        }
                    )
                return results
        except Exception:
            return []

    async def get_patent_detail(self, patent_number: str) -> dict | None:
        """Fetch detailed patent information."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                url = f"https://patents.google.com/patent/{patent_number}/en"
                headers = {
                    "User-Agent": "Mozilla/5.0 (compatible; PatentSearch/1.0)",
                    "Accept": "text/html,application/json",
                }
                # Try JSON API first
                api_url = f"https://patents.google.com/patent/{patent_number}/en?format=json"
                resp = await client.get(api_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return self._parse_patent_json(data, patent_number)

                # Fallback to HTML
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return self._parse_patent_html(resp.text, patent_number)
        except Exception:
            pass
        return None

    def _parse_patent_json(self, data: dict, pn: str) -> dict:
        try:
            title = data.get("title", "")
            abstract = data.get("abstract", "")
            if isinstance(abstract, list):
                abstract = " ".join(abstract)
            return {
                "patent_number": pn,
                "title": title[:300],
                "abstract": abstract[:1000],
                "ipc_codes": data.get("classifications", [])[:10],
                "applicants": data.get("assignee", []),
                "inventors": data.get("inventor", []),
                "publication_date": data.get("publicationDate", ""),
                "google_url": f"https://patents.google.com/patent/{pn}/en",
                "espacenet_url": f"https://worldwide.espacenet.com/patent/search?q=pn%3D{pn}",
            }
        except Exception:
            return {}

    def _parse_patent_html(self, html: str, pn: str) -> dict:
        import re

        title_match = re.search(r'<title>(.*?)</title>', html)
        title = title_match.group(1) if title_match else pn
        return {
            "patent_number": pn,
            "title": title[:300],
            "abstract": "",
            "google_url": f"https://patents.google.com/patent/{pn}/en",
            "espacenet_url": f"https://worldwide.espacenet.com/patent/search?q=pn%3D{pn}",
        }


google_patents = GooglePatentsProvider()
