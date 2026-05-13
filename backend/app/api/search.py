import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.patent import SearchIntentRequest, PatentSearchResult
from app.db.session import get_db
from app.agents.patent_extractor import patent_extractor
from app.agents.similarity_agent import similarity_agent
from app.core.config import settings
from app.search.providers import MultiSourceSearcher
from pydantic import BaseModel

router = APIRouter()


def _get_searcher() -> MultiSourceSearcher:
    return MultiSourceSearcher(serpapi_key=settings.SERPAPI_KEY)


@router.post("/intent")
async def search_by_intent(request: SearchIntentRequest):
    """F1: 全球专利搜索 — 多数据源并行 (Google Patents + Espacenet + Lens)"""
    searcher = _get_searcher()
    all_results = await searcher.search_all(request.query, num=request.top_k)

    return {
        "query": request.query,
        "total": len(all_results),
        "results": [r.to_dict() for r in all_results],
        "sources_used": list(set(r.source for r in all_results)),
    }


@router.post("/intent/stream")
async def search_by_intent_stream(request: SearchIntentRequest):
    """F1: SSE 流式搜索 — 实时推送搜索进度"""

    async def event_stream():
        query = request.query

        # Step 1: Intent parsing
        yield _sse_event("intent_start", {"message": "正在分析检索意图..."})
        plan = await search_agent.parse_intent(query)
        yield _sse_event(
            "intent_done",
            {
                "technical_field": plan.technical_field,
                "core_features": plan.core_features,
                "keywords": plan.keywords,
                "ipc_codes": plan.ipc_codes,
                "expanded_queries": plan.expanded_queries,
            },
        )

        # Step 2: Searching
        yield _sse_event("search_start", {"message": "正在执行混合检索..."})
        candidates = await search_agent.hybrid_search(plan)
        yield _sse_event(
            "search_progress",
            {"found": len(candidates), "message": f"已找到 {len(candidates)} 条候选"},
        )

        # Step 3: Re-ranking
        yield _sse_event("rerank_start", {"message": "正在AI重排序..."})
        ranked = await search_agent.rerank_with_llm(query, plan, candidates)
        yield _sse_event(
            "search_results",
            {
                "results": [
                    patent_store.populate(
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
                    )
                    for r in ranked[:20]
                ]
            },
        )

        # Step 4: Analysis
        yield _sse_event("analysis_start", {"message": "正在生成分析报告..."})
        analysis = await search_agent.generate_analysis(query, plan, ranked)
        yield _sse_event("analysis", {"text": analysis})

        yield _sse_event("done", {"total": len(ranked)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class SimilarSearchRequest(BaseModel):
    text: str
    top_k: int = 10


@router.post("/similar")
async def search_similar(request: SimilarSearchRequest):
    """F3: 上传专利找相似 — 全管线"""
    features = await patent_extractor.extract(request.text)
    result = await similarity_agent.run_full_pipeline(
        request.text, features, request.top_k
    )
    for r in result.get("results", []):
        patent_store.populate(r)
    return result


@router.post("/similar/stream")
async def search_similar_stream(request: SimilarSearchRequest):
    """F3: SSE 流式相似度检索 — 实时推送进度"""

    async def event_stream():
        text = request.text
        top_k = request.top_k

        # Step 1: Extract features
        yield _sse_event("extract_start", {"message": "正在提取专利技术特征..."})
        features = await patent_extractor.extract(text)
        yield _sse_event(
            "extract_done",
            {
                "title": features.title,
                "technical_field": features.technical_field,
                "core_innovations": features.core_innovations,
                "ipc_codes": features.ipc_codes,
                "keywords": features.keywords,
                "problem_statement": features.problem_statement,
                "technical_solution": features.technical_solution,
            },
        )

        # Step 2: Similarity search
        yield _sse_event("search_start", {"message": "正在检索相似专利..."})
        candidates = await similarity_agent.search_similar(features, text, top_k)
        yield _sse_event(
            "search_progress",
            {"found": len(candidates), "message": f"找到 {len(candidates)} 条相似专利"},
        )

        # Step 3: Results first (before comparison, for instant display)
        yield _sse_event(
            "search_results",
            {
                "results": [
                    patent_store.populate(
                        {
                            "patent_number": r.patent_number,
                            "title": r.title,
                            "abstract": r.abstract,
                            "similarity_score": round(r.similarity_score * 100, 1),
                            "ipc_codes": r.ipc_codes,
                            "applicants": r.applicants,
                        }
                    )
                    for r in candidates[:top_k]
                ]
            },
        )

        # Step 4: AI comparison (one by one)
        yield _sse_event("compare_start", {"message": "正在进行AI对比分析..."})
        compared = await similarity_agent.compare_patents(features, candidates)
        for i, r in enumerate(compared):
            yield _sse_event(
                "comparison_result",
                {
                    "index": i,
                    "patent_number": r.patent_number,
                    "comparison": r.comparison,
                    "tech_overlap": r.tech_overlap,
                    "claim_overlap": r.claim_overlap,
                    "differences": r.differences,
                },
            )

        # Step 5: Summary
        yield _sse_event("summary_start", {"message": "正在生成分析总结..."})
        summary = await similarity_agent.generate_summary(features, compared)
        yield _sse_event("summary", {"text": summary})

        yield _sse_event("done", {"total": len(compared)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
