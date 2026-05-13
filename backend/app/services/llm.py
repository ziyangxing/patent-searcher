from typing import AsyncIterator
import litellm
from app.core.config import settings


class LLMService:
    def __init__(self):
        self.default_model = self._resolve_model()

    def _resolve_model(self) -> str:
        p = settings.LLM_PROVIDER
        m = settings.LLM_MODEL
        if p == "deepseek":
            return f"openai/{m}"
        return f"{p}/{m}" if p != "openai" else f"openai/{m}"

    def _kwargs(self) -> dict:
        k = {}
        if settings.LLM_PROVIDER == "deepseek":
            k["api_base"] = settings.OPENAI_BASE_URL
        if settings.OPENAI_API_KEY:
            k["api_key"] = settings.OPENAI_API_KEY
        return k

    async def complete(
        self, prompt: str, system_prompt: str | None = None,
        model: str | None = None, temperature: float = 0.2, max_tokens: int = 2048,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await litellm.acompletion(
            model=model or self.default_model, messages=messages,
            temperature=temperature, max_tokens=max_tokens, **self._kwargs(),
        )
        return response.choices[0].message.content

    async def stream_complete(
        self, prompt: str, system_prompt: str | None = None,
        model: str | None = None, temperature: float = 0.2, max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await litellm.acompletion(
            model=model or self.default_model, messages=messages,
            temperature=temperature, max_tokens=max_tokens, stream=True, **self._kwargs(),
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


llm_service = LLMService()
