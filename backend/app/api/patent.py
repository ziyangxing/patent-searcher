import re
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response
from app.schemas.patent import (
    ParsedPatentResponse,
    PatentNumberInfo,
    PatentDetail,
    PatentBatchRequest,
)
from app.services.patent_parser import parse_patent_number
from app.services.epo_client import epo_client
from app.search.patent_provider import google_patents

router = APIRouter()


@router.get("/{patent_number}", response_model=ParsedPatentResponse)
async def get_patent_by_number(patent_number: str):
    """F2: 专利号精准检索"""
    parsed = parse_patent_number(patent_number)

    info = PatentNumberInfo(
        raw=parsed.raw,
        normalized=parsed.raw.upper().replace(" ", ""),
        country=parsed.country,
        country_name=parsed.country_name,
        kind=parsed.kind,
        is_valid=parsed.is_valid,
        error=parsed.error,
    )

    if not parsed.is_valid:
        return ParsedPatentResponse(patent_number_info=info, detail=None, family=None)

    # Try Google Patents first (no API key needed)
    detail = None
    try:
        gp_data = await google_patents.get_patent_detail(parsed.raw)
        if gp_data:
            detail = PatentDetail(
                id=0,
                patent_number=gp_data.get("patent_number", parsed.raw),
                title=gp_data.get("title", ""),
                abstract=gp_data.get("abstract", ""),
                ipc_codes=gp_data.get("ipc_codes"),
                applicants=gp_data.get("applicants"),
                inventors=gp_data.get("inventors"),
                publication_date=gp_data.get("publication_date"),
                source="google_patents",
            )
    except Exception:
        pass

    # Try EPO OPS API as fallback
    if not detail:
        biblio_data = await epo_client.get_patent_biblio(parsed.raw)
        if biblio_data:
            detail = _parse_epo_biblio(biblio_data, parsed.raw)

    family = None
    family_data = await epo_client.get_patent_family(parsed.raw)
    if family_data:
        family = _parse_epo_family(family_data)

    return ParsedPatentResponse(
        patent_number_info=info, detail=detail, family=family
    )


@router.get("/{patent_number}/download")
async def download_patent_pdf(patent_number: str):
    """Download patent PDF from Google Patents."""
    pn = patent_number.strip().upper()
    headers = {"User-Agent": "Mozilla/5.0"}

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        # Get patent page to find PDF URL
        resp = await client.get(f"https://patents.google.com/patent/{pn}/en", headers=headers)
        pdf_urls = re.findall(
            r"https://patentimages\.storage\.googleapis\.com/[^\"'\s]+\.pdf",
            resp.text,
        )

        if not pdf_urls:
            raise HTTPException(status_code=404, detail="PDF not available for this patent")

        # Download PDF
        pdf_resp = await client.get(pdf_urls[0], headers=headers)
        if pdf_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Failed to download PDF")

        return Response(
            content=pdf_resp.content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pn}.pdf"},
        )


@router.post("/batch")
async def get_patents_batch(request: PatentBatchRequest):
    """批量专利号检索"""
    results = []
    for pn in request.patent_numbers:
        try:
            result = await get_patent_by_number(pn)
            results.append(result)
        except Exception:
            results.append(
                ParsedPatentResponse(
                    patent_number_info=PatentNumberInfo(
                        raw=pn,
                        normalized=pn,
                        country="",
                        country_name="",
                        kind=None,
                        is_valid=False,
                        error=f"Failed to retrieve {pn}",
                    ),
                    detail=None,
                    family=None,
                )
            )
    return {"results": results}


def _parse_epo_biblio(data: dict, patent_number: str) -> PatentDetail | None:
    try:
        ops = data.get("ops:world-patent-data", {})
        exchange = ops.get("exchange-documents", {})
        doc = exchange.get("exchange-document", {})
        if isinstance(doc, list):
            doc = doc[0]

        biblio = doc.get("bibliographic-data", {})
        pub_ref = biblio.get("publication-reference", {})
        doc_id = pub_ref.get("document-id", {})
        if isinstance(doc_id, list):
            doc_id = doc_id[0]

        country = doc_id.get("country", "")
        doc_number = doc_id.get("doc-number", "")
        kind = doc_id.get("kind", "")
        pub_date_str = doc_id.get("date")

        from datetime import date as dt_date

        pub_date = None
        if pub_date_str and len(pub_date_str) >= 8:
            try:
                pub_date = dt_date(
                    int(pub_date_str[:4]),
                    int(pub_date_str[4:6]),
                    int(pub_date_str[6:8]),
                )
            except ValueError:
                pass

        # Title
        titles = biblio.get("invention-title", [])
        if isinstance(titles, dict):
            titles = [titles]
        title = titles[0].get("$", "") if titles else ""

        # Abstract
        abstracts = doc.get("abstract", [])
        if isinstance(abstracts, dict):
            abstracts = [abstracts]
        abstract = ""
        for ab in abstracts:
            paragraphs = ab.get("p", [])
            if isinstance(paragraphs, dict):
                paragraphs = [paragraphs]
            abstract = " ".join(p.get("$", "") for p in paragraphs)

        # Inventors
        inventors_raw = biblio.get("inventors", {}).get("inventor", [])
        if isinstance(inventors_raw, dict):
            inventors_raw = [inventors_raw]
        inventors = []
        for inv in inventors_raw:
            name = inv.get("inventor-name", {})
            first = name.get("first-name", {}).get("$", "")
            last = name.get("last-name", {}).get("$", "")
            if first or last:
                inventors.append(f"{first} {last}".strip())

        # Applicants
        applicants_raw = biblio.get("applicants", {}).get("applicant", [])
        if isinstance(applicants_raw, dict):
            applicants_raw = [applicants_raw]
        applicants = []
        for app in applicants_raw:
            app_name = app.get("applicant-name", {})
            name = app_name.get("name", {}).get("$", "")
            if isinstance(name, dict):
                name = name.get("$", "")
            if name:
                applicants.append(str(name))

        # IPC/CPC
        ipc_codes = []
        ipc_raw = biblio.get("classifications-ipcr", {}).get(
            "classification-ipcr", []
        )
        if isinstance(ipc_raw, dict):
            ipc_raw = [ipc_raw]
        for ipc in ipc_raw[:5]:
            section = ipc.get("section", "")
            cls = ipc.get("class", "")
            subclass = ipc.get("subclass", "")
            group = ipc.get("main-group", "")
            subgroup = ipc.get("subgroup", "")
            ipc_codes.append(f"{section}{cls}{subclass} {group}/{subgroup}")

        cpc_codes = []
        cpc_raw = biblio.get("patent-classifications", {}).get(
            "patent-classification", []
        )
        if isinstance(cpc_raw, dict):
            cpc_raw = [cpc_raw]
        for cpc in cpc_raw[:5]:
            if cpc.get("classification-scheme", {}).get(
                "@office", ""
            ) == "CPC":
                section = cpc.get("section", "")
                cls = cpc.get("class", "")
                subclass = cpc.get("subclass", "")
                group = cpc.get("main-group", "")
                subgroup = cpc.get("subgroup", "")
                cpc_codes.append(f"{section}{cls}{subclass}{group}/{subgroup}")

        return PatentDetail(
            id=0,
            patent_number=patent_number,
            title=title,
            abstract=abstract or None,
            ipc_codes=ipc_codes or None,
            cpc_codes=cpc_codes or None,
            inventors=inventors or None,
            applicants=applicants or None,
            publication_date=pub_date,
            country=country or None,
            doc_type=kind or None,
            source="epo_ops",
        )
    except Exception:
        return None


def _parse_epo_family(data: dict) -> list[dict]:
    try:
        ops = data.get("ops:world-patent-data", {})
        family_members = (
            ops.get("ops:patent-family", {})
            .get("family-members", {})
            .get("family-member", [])
        )
        if isinstance(family_members, dict):
            family_members = [family_members]

        result = []
        for member in family_members[:50]:
            pub_ref = member.get("publication-reference", {}).get(
                "document-id", {}
            )
            if isinstance(pub_ref, list):
                pub_ref = pub_ref[0]
            result.append(
                {
                    "country": pub_ref.get("country", ""),
                    "doc_number": pub_ref.get("doc-number", ""),
                    "kind": pub_ref.get("kind", ""),
                    "date": pub_ref.get("date", ""),
                }
            )
        return result
    except Exception:
        return []
