"""In-memory patent registry for populating search results with title/abstract."""

from app.services.data_importer import SAMPLE_PATENTS


class PatentStore:
    def __init__(self):
        self._patents: dict[str, dict] = {}
        self._load_seed_data()

    def _load_seed_data(self):
        for p in SAMPLE_PATENTS:
            self._patents[p["patent_number"]] = {
                "patent_number": p["patent_number"],
                "title": p["title"],
                "abstract": p["abstract"],
                "ipc_codes": p.get("ipc_codes", []),
                "cpc_codes": p.get("cpc_codes", []),
                "applicants": p.get("applicants", []),
                "inventors": p.get("inventors", []),
                "publication_date": (
                    p["publication_date"].isoformat()
                    if p.get("publication_date")
                    else ""
                ),
                "country": p.get("country", ""),
                "doc_type": p.get("doc_type", ""),
            }

    def get(self, patent_number: str) -> dict | None:
        return self._patents.get(patent_number)

    def populate(self, result: dict) -> dict:
        """Fill in title/abstract from the store if missing, and add patent URLs."""
        pn = result.get("patent_number", "")
        info = self.get(pn)
        if info:
            if not result.get("title"):
                result["title"] = info["title"]
            if not result.get("abstract"):
                result["abstract"] = info["abstract"]
            if not result.get("ipc_codes"):
                result["ipc_codes"] = info.get("ipc_codes", [])
            if not result.get("applicants"):
                result["applicants"] = info.get("applicants", [])
            if not result.get("publication_date"):
                result["publication_date"] = info.get("publication_date", "")
        # Add patent links
        result["google_url"] = f"https://patents.google.com/patent/{pn}/en"
        result["espacenet_url"] = f"https://worldwide.espacenet.com/patent/search?q=pn%3D{pn}"
        return result

    @property
    def count(self) -> int:
        return len(self._patents)

    @property
    def all_patent_numbers(self) -> list[str]:
        return list(self._patents.keys())


patent_store = PatentStore()
