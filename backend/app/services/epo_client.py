import httpx
from app.core.config import settings


class EPOClient:
    BASE_URL = "https://ops.epo.org/3.2/rest-services"

    def __init__(self):
        self._token: str | None = None
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def _authenticate(self):
        if settings.EPO_OPS_KEY and settings.EPO_OPS_SECRET:
            client = await self._get_client()
            auth = httpx.BasicAuth(settings.EPO_OPS_KEY, settings.EPO_OPS_SECRET)
            resp = await client.post(
                "https://ops.epo.org/3.2/auth/accesstoken",
                data={"grant_type": "client_credentials"},
                auth=auth,
            )
            if resp.status_code == 200:
                self._token = resp.json().get("access_token")

    async def _request(self, endpoint: str) -> dict | None:
        if not self._token:
            await self._authenticate()
        client = await self._get_client()
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }
        try:
            resp = await client.get(f"{self.BASE_URL}/{endpoint}", headers=headers)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 401:
                self._token = None
                await self._authenticate()
                resp = await client.get(
                    f"{self.BASE_URL}/{endpoint}", headers=headers
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        return None

    async def get_patent_biblio(self, patent_number: str) -> dict | None:
        endpoint = (
            f"published-data/publication/epodoc/{patent_number.upper()}/biblio"
        )
        return await self._request(endpoint)

    async def get_patent_abstract(self, patent_number: str) -> dict | None:
        endpoint = (
            f"published-data/publication/epodoc/{patent_number.upper()}/abstract"
        )
        return await self._request(endpoint)

    async def get_patent_claims(self, patent_number: str) -> dict | None:
        endpoint = (
            f"published-data/publication/epodoc/{patent_number.upper()}/claims"
        )
        return await self._request(endpoint)

    async def get_patent_fulltext(self, patent_number: str) -> dict | None:
        endpoint = (
            f"published-data/publication/epodoc/{patent_number.upper()}/fulltext"
        )
        return await self._request(endpoint)

    async def get_patent_family(self, patent_number: str) -> dict | None:
        endpoint = f"family/publication/epodoc/{patent_number.upper()}"
        return await self._request(endpoint)

    async def close(self):
        if self._client:
            await self._client.aclose()


epo_client = EPOClient()
