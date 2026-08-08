from __future__ import annotations

from curl_cffi import BrowserTypeLiteral
from pydantic_settings import BaseSettings


class FetchSettings(BaseSettings):
    timeout: int = 30
    max_size: int = 1048576
    follow_redirects: bool = True
    user_agent: str = "YAMS/1.0"
    stealthy_headers: bool = False
    impersonate: BrowserTypeLiteral = "chrome"

    model_config = {
        "env_prefix": "YAMS_FETCH_",
        "extra": "ignore",
    }
