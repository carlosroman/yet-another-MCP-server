from __future__ import annotations

from typing import Literal

from dotenv import load_dotenv
from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings

load_dotenv()


class SearchSettings(BaseSettings):
    provider: Literal["brave", "searxng"] = "brave"
    brave_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("BRAVE_API_KEY", "brave_api_key"),
    )
    searxng_base_url: str = Field(
        default="http://localhost:8080",
        validation_alias=AliasChoices("SEARXNG_BASE_URL", "searxng_base_url"),
    )
    count: int = Field(default=10, ge=1, le=20)
    country: str = "us"
    language: str = "en"

    @model_validator(mode="after")
    def check_brave_key_required(self) -> SearchSettings:
        if self.provider == "brave" and not self.brave_api_key:
            raise ValueError("BRAVE_API_KEY is required when provider is 'brave'")
        return self

    model_config = {
        "env_prefix": "YAMS_SEARCH_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
