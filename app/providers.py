import asyncio
import time
import uuid
from abc import ABC, abstractmethod
import httpx
from .config import Settings

Message = dict[str, str]


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, messages: list[Message]) -> str: ...


class MockProvider(LLMProvider):
    async def complete(self, messages: list[Message]) -> str:
        return "Спасибо за вопрос. Уточните, пожалуйста, вашу задачу — я предложу подходящий вариант."


class ProxyAPIProvider(LLMProvider):
    def __init__(self, settings: Settings):
        if not settings.proxyapi_key:
            raise ValueError("PROXYAPI_KEY is required for proxyapi provider")
        self.settings = settings

    async def complete(self, messages: list[Message]) -> str:
        headers = {"Authorization": f"Bearer {self.settings.proxyapi_key}"}
        payload = {"model": self.settings.proxyapi_model, "messages": messages, "temperature": 0.3}
        async with httpx.AsyncClient(timeout=self.settings.request_timeout) as client:
            response = await client.post(f"{self.settings.proxyapi_base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


class GigaChatProvider(LLMProvider):
    def __init__(self, settings: Settings):
        if not settings.gigachat_auth_key:
            raise ValueError("GIGACHAT_AUTH_KEY is required for gigachat provider")
        self.settings = settings
        self._token = ""
        self._expires_at = 0.0
        self._lock = asyncio.Lock()

    async def _access_token(self) -> str:
        if self._token and time.time() < self._expires_at - 60:
            return self._token
        async with self._lock:
            if self._token and time.time() < self._expires_at - 60:
                return self._token
            headers = {
                "Authorization": f"Basic {self.settings.gigachat_auth_key}",
                "RqUID": str(uuid.uuid4()),
                "Accept": "application/json",
            }
            async with httpx.AsyncClient(timeout=self.settings.request_timeout, verify=self.settings.gigachat_verify_ssl) as client:
                response = await client.post(
                    "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
                    headers=headers,
                    data={"scope": self.settings.gigachat_scope},
                )
                response.raise_for_status()
                data = response.json()
            self._token = data["access_token"]
            expires = float(data.get("expires_at", 0))
            self._expires_at = expires / 1000 if expires > 10_000_000_000 else expires
            return self._token

    async def complete(self, messages: list[Message]) -> str:
        token = await self._access_token()
        payload = {"model": self.settings.gigachat_model, "messages": messages, "temperature": 0.3}
        async with httpx.AsyncClient(timeout=self.settings.request_timeout, verify=self.settings.gigachat_verify_ssl) as client:
            response = await client.post(
                "https://api.giga.chat/v1/chat/completions",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


def build_provider(settings: Settings) -> LLMProvider:
    providers = {"mock": MockProvider, "gigachat": GigaChatProvider, "proxyapi": ProxyAPIProvider}
    provider_name = settings.llm_provider.lower()
    try:
        return providers[provider_name](settings) if provider_name != "mock" else MockProvider()
    except KeyError as exc:
        raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}") from exc
