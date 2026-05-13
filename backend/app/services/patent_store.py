"""In-memory patent registry for populating search results with title/abstract."""

import json
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "real_patents.json")


class PatentStore:
    def __init__(self):
        self._patents: dict[str, dict] = {}
        self._load()

    def _load(self):
        if not os.path.exists(DATA_FILE):
            return
        with open(DATA_FILE, encoding="utf-8") as f:
            patents = json.load(f)
        for p in patents:
            pn = p.get("patent_number", "")
            if pn:
                self._patents[pn] = {
                    "patent_number": pn,
                    "title": p.get("title", ""),
                    "abstract": p.get("abstract", ""),
                    "ipc_codes": p.get("ipc_codes", []),
                    "applicants": [p.get("assignee", "")] if p.get("assignee") else [],
                    "inventors": [p.get("inventor", "")] if p.get("inventor") else [],
                    "publication_date": p.get("publication_date", ""),
                }

    def get(self, patent_number: str) -> dict | None:
        return self._patents.get(patent_number)

    def populate(self, result: dict) -> dict:
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
        result["google_url"] = f"https://patents.google.com/patent/{pn}/en"
        result["espacenet_url"] = f"https://worldwide.espacenet.com/patent/search?q=pn%3D{pn}"
        return result

    @property
    def count(self) -> int:
        return len(self._patents)


patent_store = PatentStore()
