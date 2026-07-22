from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    llm_provider: str = "mock"
    gigachat_auth_key: str = ""
    gigachat_scope: str = "GIGACHAT_API_B2B"
    gigachat_model: str = "GigaChat-2-Max"
    gigachat_verify_ssl: bool = True
    proxyapi_key: str = ""
    proxyapi_base_url: str = "https://api.proxyapi.ru/openai/v1"
    proxyapi_model: str = "gpt-4o-mini"
    crm_webhook_url: str = ""
    crm_webhook_token: str = ""
    internal_api_key: str = "change-me"
    request_timeout: float = 30.0
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

