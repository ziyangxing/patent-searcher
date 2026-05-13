import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.patent import Patent
from app.services.llm import llm_service
from app.services.embedding import embedding_service
from app.search.faiss_index import faiss_manager
from app.schemas.patent import PatentDetail

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


PATENT_CHAT_PROMPT = """You are a patent analyst assistant. Answer the user's question based on the patent information provided below.

Patent Details:
- Number: {patent_number}
- Title: {title}
- Abstract: {abstract}
- Claims: {claims}
- IPC Codes: {ipc_codes}
- Applicants: {applicants}
- Publication Date: {pub_date}

Similar patents found:
{similar_patents}

User question: {question}

Provide a thorough, accurate answer based on the patent data. If the patent data doesn't contain the answer, say so honestly."""


@router.post("/patent/{patent_id}")
async def chat_about_patent(
    patent_id: str,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """针对特定专利的 AI 对话"""

    async def event_stream():
        # Fetch patent from database
        patent = None
        try:
            result = await db.execute(
                select(Patent).where(Patent.patent_number == patent_id)
            )
            patent = result.scalar_one_or_none()
        except Exception:
            pass

        yield _sse("status", {"message": "正在加载专利数据..."})

        # Build patent context
        if patent:
            context = {
                "patent_number": patent.patent_number,
                "title": patent.title,
                "abstract": patent.abstract or "",
                "claims": (patent.claims or "")[:2000],
                "ipc_codes": ", ".join(patent.ipc_codes or []),
                "applicants": ", ".join(patent.applicants or []),
                "pub_date": str(patent.publication_date) if patent.publication_date else "",
            }
            yield _sse("patent_loaded", context)
        else:
            context = {
                "patent_number": patent_id,
                "title": patent_id,
                "abstract": "",
                "claims": "",
                "ipc_codes": "",
                "applicants": "",
                "pub_date": "",
            }
            yield _sse("patent_loaded", context)

        # Find similar patents
        similar_text = ""
        try:
            if faiss_manager.index is not None:
                query_text = f"{context['title']} {context['abstract']}"
                similar = faiss_manager.search(query_text, k=5)
                similar_parts = []
                for pid, score in similar:
                    if pid != patent_id:
                        similar_parts.append(f"- {pid} (similarity: {score:.2f})")
                similar_text = "\n".join(similar_parts[:3])
        except Exception:
            pass

        yield _sse("similar_found", {"patents": similar_text})

        # Generate AI response
        prompt = PATENT_CHAT_PROMPT.format(
            patent_number=context["patent_number"],
            title=context["title"],
            abstract=context["abstract"],
            claims=context["claims"],
            ipc_codes=context["ipc_codes"],
            applicants=context["applicants"],
            pub_date=context["pub_date"],
            similar_patents=similar_text or "No similar patents found.",
            question=request.message,
        )

        yield _sse("answer_start", {"message": "正在生成回答..."})

        try:
            full_response = ""
            async for chunk in llm_service.stream_complete(
                prompt=prompt,
                system_prompt="You are a patent analyst assistant.",
                temperature=0.3,
                max_tokens=1024,
            ):
                full_response += chunk
                yield _sse("answer_chunk", {"text": chunk})
        except Exception:
            fallback = (
                f"Patent {patent_id}: {context['title']}\n\n"
                f"Abstract: {context['abstract'][:500]}\n\n"
                f"For detailed analysis, please configure an LLM API key in the .env file."
            )
            yield _sse("answer_chunk", {"text": fallback})

        yield _sse("done", {"message": "回答完成"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
