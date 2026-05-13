from typing import AsyncIterator
import litellm
from app.core.config import settings


class LLMService:
    def __init__(self):
        self.default_model = self._resolve_model()

    def _resolve_model(self) -> str:
        provider = settings.LLM_PROVIDER
        model = settings.LLM_MODEL
        if provider == "openai":
            return f"openai/{model}"
        elif provider == "anthropic":
            return f"anthropic/{model}"
        elif provider == "ollama":
            return f"ollama/{model}"
        elif provider == "dashscope":
            return f"dashscope/{model}"
        return model

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await litellm.acompletion(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def stream_complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await litellm.acompletion(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def structured_complete(
        self,
        prompt: str,
        response_model: type,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.1,
    ):
        import instructor

        client = instructor.from_litellm(litellm.acompletion)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            response_model=response_model,
        )


llm_service = LLMService()
