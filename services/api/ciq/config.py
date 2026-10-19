from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    database_url: str
    query_database_url: str
    admin_database_url: str = ""
    api_key: str
    redis_url: str = ""
    agent_mode: str = "guided"
    openai_api_key: str = ""
    openai_model: str = ""
    prompt_variant: str = "evidence"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_base_url: str = "https://cloud.langfuse.com"


@lru_cache
def settings() -> Settings:
    return Settings()
