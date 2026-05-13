from pydantic import BaseModel
from datetime import date, datetime


class PatentBiblio(BaseModel):
    patent_number: str
    title: str
    abstract: str | None = None
    ipc_codes: list[str] | None = None
    cpc_codes: list[str] | None = None
    inventors: list[str] | None = None
    applicants: list[str] | None = None
    publication_date: date | None = None
    filing_date: date | None = None
    priority_date: date | None = None
    legal_status: str | None = None
    country: str | None = None
    doc_type: str | None = None
    source: str | None = None


class PatentDetail(PatentBiblio):
    id: int
    claims: str | None = None
    description: str | None = None


class PatentSearchResult(BaseModel):
    patent_number: str
    title: str
    abstract: str | None = None
    similarity_score: float | None = None
    ipc_codes: list[str] | None = None
    applicants: list[str] | None = None
    publication_date: str | None = None


class SearchIntentRequest(BaseModel):
    query: str
    top_k: int = 20
    filters: dict | None = None


class SearchSimilarRequest(BaseModel):
    top_k: int = 10
    threshold: float = 0.5


class PatentBatchRequest(BaseModel):
    patent_numbers: list[str]


class PatentNumberInfo(BaseModel):
    raw: str
    normalized: str
    country: str
    country_name: str
    kind: str | None
    is_valid: bool
    error: str | None = None


class ParsedPatentResponse(BaseModel):
    patent_number_info: PatentNumberInfo
    detail: PatentDetail | None = None
    family: list[dict] | None = None


class SearchHistoryItem(BaseModel):
    id: int
    query_type: str | None = None
    query_text: str | None = None
    results_count: int | None = None
    created_at: datetime


class UploadedDocResponse(BaseModel):
    id: int
    original_name: str | None = None
    file_type: str | None = None
    extracted_text: str | None = None
    patent_number: str | None = None
    status: str | None = None
    created_at: datetime
