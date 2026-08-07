from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class FetchResponse:
    url: str
    content: str
    content_type: str
    status_code: int
    title: str | None = None
    extracted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = field(default_factory=dict)


class ContentConverter(ABC):
    @abstractmethod
    def convert(self, content: bytes | str, content_type: str) -> str: ...


class Fetcher(ABC):
    @abstractmethod
    async def fetch(self, url: str) -> FetchResponse: ...
