from elasticsearch import AsyncElasticsearch
from app.core.config import settings


class ElasticsearchClient:
    def __init__(self):
        self.client: AsyncElasticsearch | None = None

    async def connect(self):
        self.client = AsyncElasticsearch(settings.ES_HOST)
        if not await self.client.ping():
            raise ConnectionError("Elasticsearch is not available")

    async def close(self):
        if self.client:
            await self.client.close()

    async def create_index(self):
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "patent_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop", "stemmer"],
                        }
                    }
                },
            },
            "mappings": {
                "properties": {
                    "patent_number": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "patent_analyzer",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "abstract": {
                        "type": "text",
                        "analyzer": "patent_analyzer",
                    },
                    "claims": {
                        "type": "text",
                        "analyzer": "patent_analyzer",
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "patent_analyzer",
                    },
                    "ipc_codes": {"type": "keyword"},
                    "cpc_codes": {"type": "keyword"},
                    "inventors": {"type": "keyword"},
                    "applicants": {"type": "keyword"},
                    "publication_date": {"type": "date"},
                    "filing_date": {"type": "date"},
                    "country": {"type": "keyword"},
                    "doc_type": {"type": "keyword"},
                    "legal_status": {"type": "keyword"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": settings.FAISS_DIM,
                        "index": True,
                        "similarity": "cosine",
                    },
                }
            },
        }
        if not await self.client.indices.exists(index=settings.ES_INDEX_NAME):
            await self.client.indices.create(index=settings.ES_INDEX_NAME, body=mapping)

    async def index_patent(self, patent: dict):
        await self.client.index(
            index=settings.ES_INDEX_NAME,
            id=patent.get("patent_number"),
            document=patent,
        )

    async def search_keyword(
        self,
        query: str,
        fields: list[str] | None = None,
        filters: dict | None = None,
        size: int = 10,
        offset: int = 0,
    ) -> dict:
        if fields is None:
            fields = ["title^3", "abstract^2", "claims^2", "description"]

        must_clauses = [{"multi_match": {"query": query, "fields": fields}}]
        filter_clauses = []

        if filters:
            if "ipc_codes" in filters:
                filter_clauses.append({"terms": {"ipc_codes": filters["ipc_codes"]}})
            if "country" in filters:
                filter_clauses.append({"term": {"country": filters["country"]}})
            if "date_from" in filters:
                filter_clauses.append(
                    {"range": {"publication_date": {"gte": filters["date_from"]}}}
                )
            if "date_to" in filters:
                filter_clauses.append(
                    {"range": {"publication_date": {"lte": filters["date_to"]}}}
                )

        body = {
            "query": {"bool": {"must": must_clauses, "filter": filter_clauses}},
            "from": offset,
            "size": size,
        }

        result = await self.client.search(index=settings.ES_INDEX_NAME, body=body)
        hits = result["hits"]["hits"]
        return {
            "total": result["hits"]["total"]["value"],
            "results": [{"_score": h["_score"], **h["_source"]} for h in hits],
        }

    async def get_by_patent_number(self, patent_number: str) -> dict | None:
        try:
            result = await self.client.get(
                index=settings.ES_INDEX_NAME, id=patent_number
            )
            return result["_source"]
        except Exception:
            return None

    async def delete_index(self):
        if await self.client.indices.exists(index=settings.ES_INDEX_NAME):
            await self.client.indices.delete(index=settings.ES_INDEX_NAME)


es_client = ElasticsearchClient()
